import time


def foo():
    time.sleep(1)

    return {"foo": 1}


def bar():
    time.sleep(2)
    raise ValueError("bad bar")


def baz():
    time.sleep(5)

    return {"baz": 1}


def qux():
    time.sleep(3)

    return {"qux": 1}


def main():
    print(foo())   # 1
    print(baz())   # 5
    print(qux())   # 3
    # bar()


if __name__ == "__main__":
    start = time.perf_counter()

    main()

    end = time.perf_counter()  # 종료 시간 저장
    print(f"소요 시간: {end - start:.5f}초")
