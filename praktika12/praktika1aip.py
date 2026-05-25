from collections import Counter

ips = []
status_all = []
paths = []
total_size = 0

with open('logs.txt') as f:
    for line in f:
        # Ищем статус и размер после пути (сразу после HTTP/x.x")
        match_start = line.find('HTTP/')
        if match_start == -1:
            continue
        # После HTTP/x.x" идут статус и размер
        rest = line[match_start:].split('"')[1].strip()
        parts_rest = rest.split()
        if len(parts_rest) < 2:
            continue
        status = parts_rest[0]
        try:
            size = int(parts_rest[1])
        except ValueError:
            size = 0

        # IP - первый элемент строки
        ip = line.split()[0]

        # Путь - между первым и вторым кавычками, второй элемент
        quote_start = line.find('"')
        quote_end = line.find('"', quote_start + 1)
        if quote_start == -1 or quote_end == -1:
            continue
        request = line[quote_start+1:quote_end]
        path = request.split()[1] if len(request.split()) > 1 else '/'

        ips.append(ip)
        status_all.append(status)
        paths.append(path)
        total_size += size

total_requests = len(ips)

print("Топ-5 IP-адресов:")
for ip, count in Counter(ips).most_common(5):
    print(f'{ip} - {count} запросов {round(count / total_requests * 100, 2)}%')

print("\nСтатус-коды:")
for stat, count in Counter(status_all).most_common():
    print(f'{stat} - {count} запросов {round(count / total_requests * 100, 2)}%')

print("\nСамые популярные пути:")
for url, count in Counter(paths).most_common(5):
    print(f'{url} - {count} запросов {round(count / total_requests * 100, 2)}%')

print("\nОбщий размер всех запросов:")
print(total_size)
