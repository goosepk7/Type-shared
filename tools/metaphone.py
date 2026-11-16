"""Double Metaphone (Lawrence Philips, 2000), faithful port of the reference C++ implementation.

Mirrored line-by-line in src/Shared/Speller/Metaphone.luau; tests/specs/speller.spec.luau checks the two agree on
every library key (the build stores codes, the runtime computes codes for player input, so they MUST match).
Input: any string; only ASCII letters are used. Output: (primary, secondary), each at most MAX_LEN chars.
"""

MAX_LEN = 4
VOWELS = "AEIOUY"


def double_metaphone(text: str, max_len: int = MAX_LEN):
    word = "".join(ch for ch in text.upper() if "A" <= ch <= "Z")
    length = len(word)
    if length == 0:
        return "", ""
    last = length - 1
    padded = word + "     "  # reference pads with 5 spaces so look-ahead never runs off the end
    plen = len(padded)
    pri = []
    sec = []

    def get(i):
        if 0 <= i < plen:
            return padded[i]
        return ""

    def at(start, n, *opts):
        if start < 0 or start >= plen:
            return False
        return padded[start:start + n] in opts

    def vowel(i):
        return 0 <= i < plen and padded[i] in VOWELS

    slavo = ("W" in word) or ("K" in word) or ("CZ" in word) or ("WITZ" in word)

    def add(main, alt=None):
        if alt is None:
            if main:
                pri.append(main)
                sec.append(main)
            return
        if main:
            pri.append(main)
        if alt:
            if alt[0] != " ":
                sec.append(alt)
        elif main and main[0] != " ":
            sec.append(main)

    def plen_of(parts):
        return sum(len(p) for p in parts)

    cur = 0
    if at(0, 2, "GN", "KN", "PN", "WR", "PS"):
        cur += 1
    if get(0) == "X":
        add("S")
        cur += 1

    while plen_of(pri) < max_len or plen_of(sec) < max_len:
        if cur >= length:
            break
        ch = get(cur)
        if ch in VOWELS:
            if cur == 0:
                add("A")
            cur += 1
        elif ch == "B":
            add("P")
            cur += 2 if get(cur + 1) == "B" else 1
        elif ch == "C":
            if (cur > 1 and not vowel(cur - 2) and at(cur - 1, 3, "ACH")
                    and get(cur + 2) != "I" and (get(cur + 2) != "E" or at(cur - 2, 6, "BACHER", "MACHER"))):
                add("K")
                cur += 2
            elif cur == 0 and at(cur, 6, "CAESAR"):
                add("S")
                cur += 2
            elif at(cur, 4, "CHIA"):
                add("K")
                cur += 2
            elif at(cur, 2, "CH"):
                if cur > 0 and at(cur, 4, "CHAE"):
                    add("K", "X")
                elif (cur == 0 and (at(cur + 1, 5, "HARAC", "HARIS") or at(cur + 1, 3, "HOR", "HYM", "HIA", "HEM"))
                        and not at(0, 5, "CHORE")):
                    add("K")
                elif ((at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH"))
                        or at(cur - 2, 6, "ORCHES", "ARCHIT", "ORCHID")
                        or at(cur + 2, 1, "T", "S")
                        or ((at(cur - 1, 1, "A", "O", "U", "E") or cur == 0)
                            and at(cur + 2, 1, "L", "R", "N", "M", "B", "H", "F", "V", "W", " "))):
                    add("K")
                elif cur > 0:
                    if at(0, 2, "MC"):
                        add("K")
                    else:
                        add("X", "K")
                else:
                    add("X")
                cur += 2
            elif at(cur, 2, "CZ") and not at(cur - 2, 4, "WICZ"):
                add("S", "X")
                cur += 2
            elif at(cur + 1, 3, "CIA"):
                add("X")
                cur += 3
            elif at(cur, 2, "CC") and not (cur == 1 and get(0) == "M"):
                if at(cur + 2, 1, "I", "E", "H") and not at(cur + 2, 2, "HU"):
                    if (cur == 1 and get(cur - 1) == "A") or at(cur - 1, 5, "UCCEE", "UCCES"):
                        add("KS")
                    else:
                        add("X")
                    cur += 3
                else:
                    add("K")
                    cur += 2
            elif at(cur, 2, "CK", "CG", "CQ"):
                add("K")
                cur += 2
            elif at(cur, 2, "CI", "CE", "CY"):
                if at(cur, 3, "CIO", "CIE", "CIA"):
                    add("S", "X")
                else:
                    add("S")
                cur += 2
            else:
                add("K")
                if at(cur + 1, 2, " C", " Q", " G"):
                    cur += 3
                elif at(cur + 1, 1, "C", "K", "Q") and not at(cur + 1, 2, "CE", "CI"):
                    cur += 2
                else:
                    cur += 1
        elif ch == "D":
            if at(cur, 2, "DG"):
                if at(cur + 2, 1, "I", "E", "Y"):
                    add("J")
                    cur += 3
                else:
                    add("TK")
                    cur += 2
            elif at(cur, 2, "DT", "DD"):
                add("T")
                cur += 2
            else:
                add("T")
                cur += 1
        elif ch == "F":
            cur += 2 if get(cur + 1) == "F" else 1
            add("F")
        elif ch == "G":
            if get(cur + 1) == "H":
                if cur > 0 and not vowel(cur - 1):
                    add("K")
                    cur += 2
                elif cur == 0:
                    add("J" if get(cur + 2) == "I" else "K")
                    cur += 2
                elif ((cur > 1 and at(cur - 2, 1, "B", "H", "D"))
                        or (cur > 2 and at(cur - 3, 1, "B", "H", "D"))
                        or (cur > 3 and at(cur - 4, 1, "B", "H"))):
                    cur += 2
                else:
                    if cur > 2 and get(cur - 1) == "U" and at(cur - 3, 1, "C", "G", "L", "R", "T"):
                        add("F")
                    elif cur > 0 and get(cur - 1) != "I":
                        add("K")
                    cur += 2
            elif get(cur + 1) == "N":
                if cur == 1 and vowel(0) and not slavo:
                    add("KN", "N")
                elif not at(cur + 2, 2, "EY") and get(cur + 1) != "Y" and not slavo:
                    add("N", "KN")
                else:
                    add("KN")
                cur += 2
            elif at(cur + 1, 2, "LI") and not slavo:
                add("KL", "L")
                cur += 2
            elif cur == 0 and (get(cur + 1) == "Y" or at(cur + 1, 2, "ES", "EP", "EB", "EL", "EY", "IB", "IL", "IN", "IE", "EI", "ER")):
                add("K", "J")
                cur += 2
            elif ((at(cur + 1, 2, "ER") or get(cur + 1) == "Y")
                    and not at(0, 6, "DANGER", "RANGER", "MANGER")
                    and not at(cur - 1, 1, "E", "I") and not at(cur - 1, 3, "RGY", "OGY")):
                add("K", "J")
                cur += 2
            elif at(cur + 1, 1, "E", "I", "Y") or at(cur - 1, 4, "AGGI", "OGGI"):
                if (at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH")) or at(cur + 1, 2, "ET"):
                    add("K")
                elif at(cur + 1, 4, "IER "):
                    add("J")
                else:
                    add("J", "K")
                cur += 2
            else:
                cur += 2 if get(cur + 1) == "G" else 1
                add("K")
        elif ch == "H":
            if (cur == 0 or vowel(cur - 1)) and vowel(cur + 1):
                add("H")
                cur += 2
            else:
                cur += 1
        elif ch == "J":
            if at(cur, 4, "JOSE") or at(0, 4, "SAN "):
                if (cur == 0 and get(cur + 4) == " ") or at(0, 4, "SAN "):
                    add("H")
                else:
                    add("J", "H")
                cur += 1
            else:
                if cur == 0 and not at(cur, 4, "JOSE"):
                    add("J", "A")
                elif vowel(cur - 1) and not slavo and (get(cur + 1) == "A" or get(cur + 1) == "O"):
                    add("J", "H")
                elif cur == last:
                    add("J", " ")
                elif not at(cur + 1, 1, "L", "T", "K", "S", "N", "M", "B", "Z") and not at(cur - 1, 1, "S", "K", "L"):
                    add("J")
                cur += 2 if get(cur + 1) == "J" else 1
        elif ch == "K":
            cur += 2 if get(cur + 1) == "K" else 1
            add("K")
        elif ch == "L":
            if get(cur + 1) == "L":
                if ((cur == length - 3 and at(cur - 1, 4, "ILLO", "ILLA", "ALLE"))
                        or ((at(last - 1, 2, "AS", "OS") or at(last, 1, "A", "O")) and at(cur - 1, 4, "ALLE"))):
                    add("L", " ")
                    cur += 2
                    continue
                cur += 2
            else:
                cur += 1
            add("L")
        elif ch == "M":
            if (at(cur - 1, 3, "UMB") and (cur + 1 == last or at(cur + 2, 2, "ER"))) or get(cur + 1) == "M":
                cur += 2
            else:
                cur += 1
            add("M")
        elif ch == "N":
            cur += 2 if get(cur + 1) == "N" else 1
            add("N")
        elif ch == "P":
            if get(cur + 1) == "H":
                add("F")
                cur += 2
            else:
                cur += 2 if at(cur + 1, 1, "P", "B") else 1
                add("P")
        elif ch == "Q":
            cur += 2 if get(cur + 1) == "Q" else 1
            add("K")
        elif ch == "R":
            if cur == last and not slavo and at(cur - 2, 2, "IE") and not at(cur - 4, 2, "ME", "MA"):
                add("", "R")
            else:
                add("R")
            cur += 2 if get(cur + 1) == "R" else 1
        elif ch == "S":
            if at(cur - 1, 3, "ISL", "YSL"):
                cur += 1
            elif cur == 0 and at(cur, 5, "SUGAR"):
                add("X", "S")
                cur += 1
            elif at(cur, 2, "SH"):
                if at(cur + 1, 4, "HEIM", "HOEK", "HOLM", "HOLZ"):
                    add("S")
                else:
                    add("X")
                cur += 2
            elif at(cur, 3, "SIO", "SIA") or at(cur, 4, "SIAN"):
                if not slavo:
                    add("S", "X")
                else:
                    add("S")
                cur += 3
            elif (cur == 0 and at(cur + 1, 1, "M", "N", "L", "W")) or at(cur + 1, 1, "Z"):
                add("S", "X")
                cur += 2 if at(cur + 1, 1, "Z") else 1
            elif at(cur, 2, "SC"):
                if get(cur + 2) == "H":
                    if at(cur + 3, 2, "OO", "ER", "EN", "UY", "ED", "EM"):
                        if at(cur + 3, 2, "ER", "EN"):
                            add("X", "SK")
                        else:
                            add("SK")
                    else:
                        if cur == 0 and not vowel(3) and get(3) != "W":
                            add("X", "S")
                        else:
                            add("X")
                    cur += 3
                elif at(cur + 2, 1, "I", "E", "Y"):
                    add("S")
                    cur += 3
                else:
                    add("SK")
                    cur += 3
            else:
                if cur == last and at(cur - 2, 2, "AI", "OI"):
                    add("", "S")
                else:
                    add("S")
                cur += 2 if at(cur + 1, 1, "S", "Z") else 1
        elif ch == "T":
            if at(cur, 4, "TION"):
                add("X")
                cur += 3
            elif at(cur, 3, "TIA", "TCH"):
                add("X")
                cur += 3
            elif at(cur, 2, "TH") or at(cur, 3, "TTH"):
                if at(cur + 2, 2, "OM", "AM") or at(0, 4, "VAN ", "VON ") or at(0, 3, "SCH"):
                    add("T")
                else:
                    add("0", "T")
                cur += 2
            else:
                cur += 2 if at(cur + 1, 1, "T", "D") else 1
                add("T")
        elif ch == "V":
            cur += 2 if get(cur + 1) == "V" else 1
            add("F")
        elif ch == "W":
            if at(cur, 2, "WR"):
                add("R")
                cur += 2
            else:
                if cur == 0 and (vowel(cur + 1) or at(cur, 2, "WH")):
                    if vowel(cur + 1):
                        add("A", "F")
                    else:
                        add("A")
                if ((cur == last and vowel(cur - 1)) or at(cur - 1, 5, "EWSKI", "EWSKY", "OWSKI", "OWSKY")
                        or at(0, 3, "SCH")):
                    add("", "F")
                    cur += 1
                elif at(cur, 4, "WICZ", "WITZ"):
                    add("TS", "FX")
                    cur += 4
                else:
                    cur += 1
        elif ch == "X":
            if not (cur == last and (at(cur - 3, 3, "IAU", "EAU") or at(cur - 2, 2, "AU", "OU"))):
                add("KS")
            cur += 2 if at(cur + 1, 1, "C", "X") else 1
        elif ch == "Z":
            if get(cur + 1) == "H":
                add("J")
                cur += 2
            else:
                if at(cur + 1, 2, "ZO", "ZI", "ZA") or (slavo and cur > 0 and get(cur - 1) != "T"):
                    add("S", "TS")
                else:
                    add("S")
                cur += 2 if get(cur + 1) == "Z" else 1
        else:
            cur += 1

    p = "".join(pri)[:max_len]
    s = "".join(sec)[:max_len]
    return p, s


if __name__ == "__main__":
    import sys
    for w in sys.argv[1:]:
        print(w, double_metaphone(w))
