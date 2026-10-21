import re
with open("tests/test_tools_security.py", "r") as f:
    content = f.read()

# remove the later import os/pytest
content = content.replace("import os\n\nimport pytest\n", "")
# add it at the top
content = "import os\nimport pytest\n\n" + content

with open("tests/test_tools_security.py", "w") as f:
    f.write(content)
