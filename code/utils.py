def escape_filename(name):
    encoding = {
        ':': '%3A',
        '<': '%3C',
        '>': '%3E',
        '*': '%2A',
        '?': '%3F',
        '|': '%7C',
        '-': '%2D',
        '"': '%22'
    }
    for c in encoding:
        name = name.replace(c, encoding[c])
    return name.replace(' ', '-')

def escape(s):
    return s.replace('#', '&num;') if s else ''

def encode_special_chars(s):
    return s.replace('#', '{specialchar_num}') if s else ''

def decode_special_chars(s):
    return s.replace('{specialchar_num}', '#')