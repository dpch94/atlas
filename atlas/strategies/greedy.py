import numpy as np

from queue import PriorityQueue
from typing import List, Tuple, Set, Callable, Optional

from atlas import Strategy
from atlas.exceptions import ExceptionAsContinue
from atlas.models import GeneratorModel
from atlas.operators import OpInfo


class GreedyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.call_id: int = 0
        self.forwarding_map: List[int] = []
        self.score_map: List[float] = []
        self.finished: bool = False
        self.worklist: PriorityQueue = PriorityQueue()
        self.explored: Set[Tuple[int, ...]] = set()

    def is_finished(self):
        return self.finished

    def init(self):
        self.call_id = 0
        self.forwarding_map = {}
        self.score_map = {}
        self.finished = False
        self.worklist = PriorityQueue()
        self.explored = set()

        self.worklist.put((0, [], []))

    def init_run(self):
        self.call_id = 0
        _, self.forwarding_map, self.score_map = self.worklist.get()
        self.forwarding_map = self.forwarding_map[:]
        self.score_map = self.score_map[:]

    def finish_run(self):
        if self.forwarding_map is not None:
            cum_prod_forward = np.cumprod(self.score_map)
            cum_prod_backward = np.cumprod(self.score_map[::-1])[::-1]

            for idx in range(len(self.forwarding_map)):
                score = (cum_prod_forward[idx-1] if idx > 0 else 1.0) * (cum_prod_backward[idx+1] if idx + 1 < len(self.forwarding_map) else 1.0)
                forwarding = self.forwarding_map[:idx] + [self.forwarding_map[idx] + 1]

                key = tuple(forwarding)
                if key in self.explored:
                    continue

                self.explored.add(key)
                scores = self.score_map[:idx] + [0.0]  # We don't know the score of the next prediction
                self.worklist.put((-score, forwarding, scores))

        if self.worklist.empty():
            self.finished = True

    def generic_op(self, domain=None, context=None, model: GeneratorModel = None,
                   op_info: OpInfo = None, handler: Optional[Callable] = None,
                   **kwargs):
        t = self.call_id
        self.call_id += 1

        if len(self.forwarding_map) > t:
            iterator = iter(handler(self, domain=domain, context=context, op_info=op_info, model=model, **kwargs))

            try:
                val, score = next(iterator)
                for _ in range(self.forwarding_map[t]):  # 0-indexed
                    val, score = next(iterator)

                self.score_map[t] = score
                return val

            except StopIteration:
                #  Ran out of possibilities, this forwarding map is infeasible
                self.forwarding_map = None
                raise ExceptionAsContinue

        else:
            #  Need to start fresh
            iterator = iter(handler(self, domain=domain, context=context, op_info=op_info, model=model, **kwargs))
            val, score = next(iterator)
            self.forwarding_map.append(0)
            self.score_map.append(score)

            return val
