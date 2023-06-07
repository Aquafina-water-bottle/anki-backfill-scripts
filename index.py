import re
from dataclasses import dataclass

rx_WHITESPACE = re.compile(r"\s+")

def preprocess_line(line: str, remove_whitespace=True):
    result = line
    if remove_whitespace:
        result = rx_WHITESPACE.sub("", result)
    return result

@dataclass
class LineIndex:
    original_line: str
    processed_line: str
    index: int

class CorpusIndex:
    def __init__(self, lines: list[str]):
        self.index: list[LineIndex] = self.create_index(lines)
        self.full_str: str = "".join(x.processed_line for x in self.index)

    def create_index(self, lines: list[str], remove_whitespace=True) -> list[LineIndex]:
        result = []
        counter = 0
        for l in lines:
            # remove whitespace
            processed_line = preprocess_line(l, remove_whitespace=remove_whitespace)
            new_line: LineIndex = LineIndex(l, processed_line, counter)
            result.append(new_line)
            counter += len(processed_line)
        return result

    def find_lines(self, input_line: str) -> tuple[int, int] | None:
        pline = preprocess_line(input_line)
        if pline not in self.full_str:
            return None # string was not found
        idx = self.full_str.index(pline)
        end_idx = idx + len(pline)

        # Ideally, we'd use the bisect library to change this to o(log(n)), but I got lazy
        first_i = 0
        end_i = 0
        for i, line in enumerate(self.index):
            if line.index <= idx:
                first_i = i
            else:
                break

        for i, line in enumerate(self.index[first_i:]):
            if line.index < end_idx:
                end_i = i
            else:
                break
        end_i += first_i

        #print(first_i, end_i)
        return (first_i, end_i+1)
        #return [x.original_line for x in self.index[first_i: end_i+1]]

    def index_og_lines(self, start: int, end: int):
        return [x.original_line for x in self.index[start: end]]


if __name__ == "__main__":
    # too lazy to create proper tests, some tests are here instead!

    # some random text from https://lipsum.sugutsukaeru.jp/index.cgi
    with open("files/ipsum.txt") as f:
        sample_lines = f.read().strip().split("\n\n")

    ci = CorpusIndex(sample_lines)

    print(ci.find_lines("右底の通り後を当てるば来ありという人間は眺めまであるずから、別段空位つまらない珍社のありて始め外国は大体着けいです。"))

    print(ci.find_lines("私をこの事ませ、半分の自分がどこも会が一通り聴かでしょ、場合にはそれの幾人を聴こですというのはたとい概念のための吟味行くたのずはた。自由にあるて学校の先生へ解らずのたまし。"))

    print(ci.find_lines("私をこの事ませ、半分の自分がどこも会が一通り聴かでしょ、場合にはそれの幾人を聴こですというのはたとい概念のための吟味行くたのずはた。"))








