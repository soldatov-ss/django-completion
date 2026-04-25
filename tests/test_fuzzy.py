from django_completion.fuzzy import suggest


def test_close_match():
    commands = ["migrate", "shell", "runserver", "makemigrations"]
    assert "migrate" in suggest("migarte", commands)


def test_close_match_shell():
    commands = ["migrate", "shell", "runserver"]
    assert "shell" in suggest("shel", commands)


def test_no_match():
    commands = ["migrate", "shell", "runserver"]
    assert suggest("xyz123", commands) == []


def test_multiple_candidates():
    commands = ["migrate", "makemigrations", "showmigrations"]
    results = suggest("migr", commands, cutoff=0.4)
    assert len(results) > 0
