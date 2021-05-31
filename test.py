
exception = False

try:
    if exception:
        raise Exception('hello')

except Exception as e:
    print('except exception : ', e.__str__())

else:
    print('else')

finally:
    print('finally')