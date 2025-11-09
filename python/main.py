from lib import sum_as_string_python
from py03_benchmark.py03_benchmark import sum_as_string


def main():
    print("Hello from py03-benchmark!")
    result = sum_as_string(1, 2)
    print(result)
    result = sum_as_string_python(1, 2)
    print(result)


if __name__ == "__main__":
    main()
