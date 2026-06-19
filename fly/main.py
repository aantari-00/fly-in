import sys
from parser import Parser


def main():
    file_path = sys.argv[1]
    parser = Parser(file_path)
    print(parser.filename)


if __name__ == "__main__":
    main()