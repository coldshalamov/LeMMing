with open("tests/test_api_auth.py", "r") as f:
    c = f.read()

c = c.replace(
    "'{\"name\": \"source\", \"title\": \"Src\", \"short_description\": \"Src\", \"model\": {\"key\": \"gpt\"}, \"permissions\": {\"read_outboxes\": [], \"tools\": []}, \"schedule\": {\"run_every_n_ticks\": 1, \"phase_offset\": 0}, \"instructions\": \"test\"}'",
    "(\n"
    "            '{\"name\": \"source\", \"title\": \"Src\", \"short_description\": \"Src\", '\n"
    "            '\"model\": {\"key\": \"gpt\"}, \"permissions\": {\"read_outboxes\": [], \"tools\": []}, '\n"
    "            '\"schedule\": {\"run_every_n_ticks\": 1, \"phase_offset\": 0}, \"instructions\": \"test\"}'\n"
    "        )"
)

with open("tests/test_api_auth.py", "w") as f:
    f.write(c)
