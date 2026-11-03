$RequestPath = $env:FINAGENT_MEDIA_REQUEST
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Runtime.WindowsRuntime

function Await-WinRT($Operation, [Type]$ResultType) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and
        $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1
    $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.GetAwaiter().GetResult()
}
function Await-Action($Operation) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and
        $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
    } | Select-Object -First 1
    $task = $method.Invoke($null, @($Operation))
    $null = $task.GetAwaiter().GetResult()
}

try {
    $request = [IO.File]::ReadAllText($RequestPath) | ConvertFrom-Json
    $result = @{}
    if ($request.action -in @('inspect_pdf','render_pdf')) {
        [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null
        [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime] | Out-Null
        [Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType=WindowsRuntime] | Out-Null
        [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime] | Out-Null
        [Windows.Graphics.Imaging.BitmapEncoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime] | Out-Null
        $file = Await-WinRT ([Windows.Storage.StorageFile]::GetFileFromPathAsync($request.input_path)) ([Windows.Storage.StorageFile])
        $pdf = Await-WinRT ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
        if ($pdf.IsPasswordProtected) { throw 'PDF_ENCRYPTED' }
        $result.page_count = [int]$pdf.PageCount
        $result.password_protected = [bool]$pdf.IsPasswordProtected
        if ($pdf.PageCount -gt 300) { throw 'PAGE_LIMIT' }
        if ($request.action -eq 'inspect_pdf') {
            $pages = @()
            for ($i=0; $i -lt $pdf.PageCount; $i++) {
                $page = $pdf.GetPage([uint32]$i)
                try { $pages += @{physical_index=$i; width_dip=$page.Size.Width; height_dip=$page.Size.Height;
                                 intrinsic_rotation=([int]$page.Rotation * 90)} }
                finally { $page.Dispose() }
            }
            $result.pages = @($pages)
        } else {
            if ($request.page_index -lt 0 -or $request.page_index -ge $pdf.PageCount) { throw 'INVALID_PAGE_INDEX' }
            $page = $pdf.GetPage([uint32]$request.page_index)
            $stream = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
            try {
                # WinRT Size is in DIPs, already accounting for CropBox/MediaBox/Rotation.
                $width = [int][Math]::Ceiling($page.Size.Width * $request.dpi / 96.0)
                $height = [int][Math]::Ceiling($page.Size.Height * $request.dpi / 96.0)
                if ([double]$width * $height -gt 100000000) { throw 'RASTER_PIXEL_LIMIT' }
                $options = New-Object Windows.Data.Pdf.PdfPageRenderOptions
                [Windows.Graphics.Display.DisplayProperties, Windows.Graphics.Display, ContentType=WindowsRuntime] | Out-Null
                $logicalDpi = [double][Windows.Graphics.Display.DisplayProperties]::LogicalDpi
                if ($logicalDpi -le 0) { throw 'INVALID_LOGICAL_DPI' }
                # Destination dimensions are DIPs; compensate host scale, then check actual PNG.
                $options.DestinationWidth = [uint32][Math]::Round($width * 96.0 / $logicalDpi)
                $options.DestinationHeight = [uint32][Math]::Round($height * 96.0 / $logicalDpi)
                $options.BitmapEncoderId = [Windows.Graphics.Imaging.BitmapEncoder]::PngEncoderId
                Await-Action ($page.RenderToStreamAsync($stream,$options))
                $reader = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($stream)
                $output = [IO.File]::Open($request.output_path,[IO.FileMode]::CreateNew)
                try { $reader.CopyTo($output) } finally { $output.Dispose(); $reader.Dispose() }
                $result.width = $width; $result.height = $height
                $result.logical_dpi = $logicalDpi
                $result.width_dip = $page.Size.Width; $result.height_dip = $page.Size.Height
                $result.intrinsic_rotation = [int]$page.Rotation * 90
            } finally { $page.Dispose(); $stream.Dispose() }
        }
    } elseif ($request.action -in @('inspect_image','transform','crop','estimate_skew')) {
        $image = [System.Drawing.Bitmap]::FromFile($request.input_path)
        try {
            if ([double]$image.Width*$image.Height -gt 100000000) { throw 'RASTER_PIXEL_LIMIT' }
            $result.width = $image.Width; $result.height = $image.Height
            if ($request.action -eq 'crop') {
                $x=[int]$request.x; $y=[int]$request.y; $w=[int]$request.width; $h=[int]$request.height
                if ($x -lt 0 -or $y -lt 0 -or $w -le 0 -or $h -le 0 -or $x+$w -gt $image.Width -or $y+$h -gt $image.Height) { throw 'CROP_OUTSIDE_RASTER' }
                $crop = $image.Clone([Drawing.Rectangle]::new($x,$y,$w,$h),$image.PixelFormat)
                try { $crop.Save($request.output_path,[Drawing.Imaging.ImageFormat]::Png) }
                finally { $crop.Dispose() }
                $result.width=$w; $result.height=$h
            } elseif ($request.action -eq 'transform') {
                $w=[int]$request.width; $h=[int]$request.height
                if ($w -le 0 -or $h -le 0 -or [double]$w*$h -gt 100000000) { throw 'RASTER_PIXEL_LIMIT' }
                $m = $request.matrix
                $matrix=[Drawing.Drawing2D.Matrix]::new([float]$m.a,[float]$m.b,[float]$m.c,[float]$m.d,[float]$m.e,[float]$m.f)
                $dest=[Drawing.Bitmap]::new($w,$h)
                $graphics=[Drawing.Graphics]::FromImage($dest)
                try {
                    $graphics.Clear([Drawing.Color]::White)
                    $graphics.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $graphics.Transform=$matrix
                    $graphics.DrawImage($image,0,0,$image.Width,$image.Height)
                    $dest.Save($request.output_path,[Drawing.Imaging.ImageFormat]::Png)
                    $result.width=$w; $result.height=$h; $result.actual_matrix=@($matrix.Elements)
                } finally { $graphics.Dispose(); $dest.Dispose(); $matrix.Dispose() }
            } elseif ($request.action -eq 'estimate_skew') {
                Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
public static class ProjectionSkew {
    public static double[] Estimate(Bitmap image) {
        int step=Math.Max(1,(int)Math.Ceiling(Math.Sqrt((double)image.Width*image.Height/100000)));
        var points=new List<Point>();
        for(int y=0;y<image.Height;y+=step) for(int x=0;x<image.Width;x+=step) {
            Color p=image.GetPixel(x,y);
            if(p.R+p.G+p.B<384) points.Add(new Point(x,y));
        }
        double best=0,second=0,angle=0;
        if(points.Count<20) return new double[]{0,0,0,points.Count};
        for(int k=-20;k<=20;k++) {
            double candidate=k*0.25,rad=candidate*Math.PI/180;
            var bins=new Dictionary<int,int>();
            foreach(Point p in points) {
                int v=(int)Math.Round((Math.Sin(rad)*p.X+Math.Cos(rad)*p.Y)/step);
                int old; bins.TryGetValue(v,out old); bins[v]=old+1;
            }
            double score=0; foreach(int n in bins.Values) score+=(double)n*n;
            if(score>best) {second=best;best=score;angle=candidate;} else if(score>second) second=score;
        }
        return new double[]{angle,best,second,points.Count};
    }
}
'@
                $v=[ProjectionSkew]::Estimate($image)
                $result.angle_degrees=$v[0]; $result.projection_score=$v[1]
                $result.runner_up_score=$v[2]; $result.ink_points=[int]$v[3]
            }
        } finally { $image.Dispose() }
    } else { throw 'UNKNOWN_MEDIA_ACTION' }
    $result.ok=$true
    $result.peak_working_set_bytes=[Diagnostics.Process]::GetCurrentProcess().PeakWorkingSet64
    $result | ConvertTo-Json -Depth 8 -Compress
} catch {
    # Do not expose OS exception text (may contain input paths or document contents).
    @{ok=$false; code='WINDOWS_MEDIA_FAILED'; diagnostic_type=$_.Exception.GetType().Name;
      diagnostic_line=$_.InvocationInfo.ScriptLineNumber} | ConvertTo-Json -Compress
    exit 1
}
