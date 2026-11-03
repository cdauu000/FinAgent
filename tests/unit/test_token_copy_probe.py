from eval.token_copy_probe import prepare_dataset, score_responses


def test_probe_is_synthetic_short_aliases_with_no_measured_quality_or_threshold() -> None:
    dataset = prepare_dataset()
    assert dataset.status == "NOT_RUN" and dataset.quality_threshold is None
    assert all(len(token.split("_")[1]) == 8 for case in dataset.cases for token in case.tokens)


def test_scorer_counts_missing_wrong_and_extra_tokens_without_changing_denominator() -> None:
    dataset = prepare_dataset()
    responses = {case.id: case.tokens for case in dataset.cases}
    responses.pop(dataset.cases[-1].id)
    responses[dataset.cases[0].id] += ("ent_extra000",)
    result = score_responses(dataset, responses, model="synthetic-unit-fixture")
    assert result["missing_cases"] == 1
    assert result["total_expected_positions"] == 30
    assert result["correct_token_positions"] == 14
    assert result["exact_cases"] == 2
    assert result["extra_tokens"] == 1
    assert result["quality_threshold"] is None
    assert score_responses(dataset, {}, model="not-run")["status"] == "NOT_RUN"


def test_scorer_counts_a_wrong_alias_as_wrong_even_with_correct_array_length() -> None:
    dataset = prepare_dataset()
    responses = {case.id: case.tokens for case in dataset.cases}
    case = dataset.cases[0]
    responses[case.id] = ("ent_wrong000", *case.tokens[1:])
    result = score_responses(dataset, responses, model="synthetic-unit-fixture")
    assert result["correct_token_positions"] == 29
    assert result["total_expected_positions"] == 30
    assert result["exact_cases"] == 3
    assert result["missing_cases"] == result["extra_tokens"] == 0
