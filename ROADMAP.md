# Project Roadmap

- pywest is a tool to pack python project along with embeddable python
- no its new tool, give code for this and this tool is only for windows
- it relies heavily on pyproject.toml for packages to be installed
- it takes only one entry point
- simply running pywest will print cli informaton
- pywest project_name starts the bundling and output the zip file by default adjacent to the project_name directory
- pywest project_name, give options for bundle type to simply another folder along the project_folder where the emb python is setup
- it creates run.bat which add required env variables and run the project with embeddable python from bin dir
- it also uncomments import site section in .pth file of embeddable python
- there will be single file inside pywest folder that is main.py and there will single file inside tests folder, for now give only pyproject.toml and main.py

- [ ] More Features
