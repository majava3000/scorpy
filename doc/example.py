# this file is just an example, although ideally this would be the same
# that will generate the wavedrom stuff later

if __name__ == '__main__':
    input_ = makeSimpleTrack('input', shortcodeToSegiter("ABCA.B.C.A..B..C.."))

    # this allows us to use symbols as is, without messing stuff us. only useful
    # for examples though
    B = 66
    Y = 89
    n = 110

    # clip-start
    r1 = core.tester(input_, lambda dur, v: (v == B and dur == 2))
    r2 = core.tester(input_, lambda dur, v: (v == B and dur == 2), (Y, n))
    r3 = core.tester(input_, lambda dur, v: (dur == 2), (core.VALUE_PASSTHROUGH, n))
    r4 = core.tester(input_, lambda dur, v: (dur == 2), (Y, core.VALUE_PASSTHROUGH))
    # clip-end

    r1 = makeSimpleTrack('result1', r1)
    r2 = makeSimpleTrack('result2', r2)
    r3 = makeSimpleTrack('result3', r3)
    r4 = makeSimpleTrack('result4', r4)

    # print(resultAsWavedrom('tester', input_, (r1, r2, r3, r4)))
    printAsShortcodes([input_]+[r1, r2, r3, r4])
