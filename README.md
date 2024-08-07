# ShonenJumpPlus parser
![Static Badge](https://img.shields.io/badge/Version-1.0.0-green)
![Static Badge](https://img.shields.io/badge/build-passing-blue)
![Static Badge](https://img.shields.io/badge/-Apache--2.0_license-red)
## Dependencies
![Static Badge](https://img.shields.io/badge/Python-3.12.4-green)
![Static Badge](https://img.shields.io/badge/Poetry-1.8.3-blue)
![Static Badge](https://img.shields.io/badge/PIL-10.4.0-red)
![Static Badge](https://img.shields.io/badge/reportlab-4.2.2-white)
![Static Badge](https://img.shields.io/badge/requests-2.32.3-yellow)


## Introdaction
This parser is developed for downloading free chapters from https://shonenjumpplus.com via pdf by url of a chapter. This parser use multiprocessing technology for boosting at perfomance

## Installation
1. You need copy repository to your machine by ```git clone``` command
2. After you need execute ```poetry install``` command since the project uses poetry as a package manager
3. Next you can use default test script like 'oshinoko' by entering command ```poetry run oshinoko``` or manualy edit test.py from test folder (Also you can edit pyproject.toml and create oshinoko-like function for new ```poetry run``` command)

## Future of the project
In the future it will be modified for improving indexing process (indexing stage executes parallel with rendering to pdf but a lot of time are wasted by awaiting request of json files)
