from typing import List


def chunk_list(data: List, chunk_size: int) -> List[List]:
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
