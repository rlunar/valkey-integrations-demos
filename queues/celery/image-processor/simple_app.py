from tasks import add

result = add.delay(4, 7)
print(result.ready())
print(result.get(timeout=1))
