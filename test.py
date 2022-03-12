import remoteprotocols.codecs.parse as ptrn

t = ["header", "footer"]
a = ["arg1", "arg2", "arg3"]

p = "header (arg1 > 10 ? {arg1 LSB 8}{0 LSB 8}){arg2 LSB 9} footer"


def test(pattern):

    r = ptrn.parse_pattern(pattern, t, a)

    print(pattern)
    print(r)
    for i in r:
        print(i.__dict__)
