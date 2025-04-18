import random
import hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class QuotientFilter:
    def __init__(self, q, r):
        self.q = q                                  # число бит для quotient
        self.r = r                                  # число бит для remainder
        self.m = 1 << q                             # размер таблицы = 2^q
        # массивы для хранения остатка и трёх флагов
        self.remainders      = np.zeros(self.m, dtype=np.uint64)
        self.is_occupied     = np.zeros(self.m, dtype=bool)  # был ли занят канонический слот
        self.is_continuation = np.zeros(self.m, dtype=bool)  # продолжение run’а
        self.is_shifted      = np.zeros(self.m, dtype=bool)  # сдвинут ли remainder

    def _hash(self, x):
        # получаем 256‑битный SHA256 и переводим в целое
        return int(hashlib.sha256(str(x).encode()).hexdigest(), 16)

    def _decode(self, h):
        # оставляем только p = q+r младших бит для quotient и remainder
        p = self.q + self.r
        h_trunc = h & ((1 << p) - 1)             # обрезаем до p бит
        q = h_trunc >> self.r                    # старшие q бит → индекс регистра
        r = h_trunc & ((1 << self.r) - 1)        # младшие r бит → остаток
        return q, r

    def _find_cluster_start(self, idx):
        # поиск начала кластера: двигаемся влево, пока видим сдвинутые элементы
        i = idx
        while self.is_shifted[i]:
            i = (i - 1) % self.m
        return i

    def _find_run_start(self, q):
        # находим run для данного quotient внутри кластера
        cluster_start = self._find_cluster_start(q)
        # считаем, сколько run’ов расположено до q
        run_count = np.count_nonzero(self.is_occupied[:q])
        i, curr = cluster_start, 0
        while True:
            if self.is_occupied[i]:
                if curr == run_count:
                    return i                      # нашли начало нужного run’а
                curr += 1
            i = (i + 1) % self.m

    def add(self, x):
        h = self._hash(x)
        q, r = self._decode(h)
        # если слот полностью свободен — просто вставляем и ставим occupied
        if not (self.is_occupied[q] or self.is_shifted[q] or self.is_continuation[q]):
            self.remainders[q]      = r
            self.is_occupied[q]     = True
            return

        # иначе помечаем occupied и начинаем вставку в соответствующий run
        self.is_occupied[q] = True
        run_start = self._find_run_start(q)

        # ищем позицию по возрастанию остатков
        pos = run_start
        first = True
        while first or self.is_continuation[pos]:
            if self.remainders[pos] > r:
                break
            pos = (pos + 1) % self.m
            first = False

        # сдвигаем вправо всё до ближайшей свободной ячейки
        j = pos
        while self.is_occupied[j] or self.is_shifted[j] or self.is_continuation[j]:
            j = (j + 1) % self.m
        k = j
        while k != pos:
            prev = (k - 1) % self.m
            # переносим данные и флаги со сдвигом
            self.remainders[k]      = self.remainders[prev]
            self.is_continuation[k] = self.is_continuation[prev]
            self.is_shifted[k]      = True
            k = prev

        # вставляем новый остаток в освободившуюся позицию
        self.remainders[pos]      = r
        self.is_continuation[pos] = (pos != run_start)

    def lookup(self, x):
        h = self._hash(x)
        q, r = self._decode(h)
        # если в каноническом слоте нет occupied → точно нет
        if not self.is_occupied[q]:
            return False
        # ищем начало run’а и пробегаем его
        start = self._find_run_start(q)
        i = start
        while True:
            if self.remainders[i] == r:
                return True                     # нашли совпадение
            i = (i + 1) % self.m
            if not self.is_continuation[i]:
                break                          # конец run’а
        return False                             # не найдено

    def __contains__(self, x):
        return self.lookup(x)

# Функция для измерения ложноположительных срабатываний
def run_experiment(q, r, alpha, n_queries=10000):
    m = 1 << q
    n = int(alpha * m)
    qf = QuotientFilter(q, r)
    
    # Вставка
    inserted = set()
    while len(inserted) < n:
        inserted.add(random.randrange(0, 10 * m))
    for x in inserted:
        qf.add(x)
    
    # Генерация запросов
    queries = []
    while len(queries) < n_queries:
        x = random.randrange(0, 10 * m)
        if x not in inserted:
            queries.append(x)
    
    fp = sum(1 for x in queries if x in qf)
    return fp / n_queries


q_values = [10]
r_values = [4, 6, 8, 10]
alpha_values = [0.2, 0.4, 0.6, 0.8]


results = []
for q in q_values:
    for r in r_values:
        for alpha in alpha_values:
            rate = run_experiment(q, r, alpha)
            results.append({
                'q': q,
                'r': r,
                'load_factor': alpha,
                'false_positive_rate': rate
            })

df = pd.DataFrame(results)

# График зависимости
plt.figure()
for r in r_values:
    subset = df[df['r'] == r]
    plt.plot(subset['load_factor'], subset['false_positive_rate'], marker='o', label=f'r={r}')
plt.xlabel('Коэффициент заполнения (α)')
plt.ylabel('Вероятность ложноположительного срабатывания')
plt.title('Зависимость вероятности ложноположительного срабатывания от α')
plt.legend()
plt.show()
