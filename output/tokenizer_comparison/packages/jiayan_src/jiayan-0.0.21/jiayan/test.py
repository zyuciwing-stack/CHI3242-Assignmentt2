import random



def test():
    global total
    for i in range(10):
        total += 1
        yield i

def pos_train():
    from jiayan import load_lm
    from jiayan import CharHMMTokenizer
    from jiayan.utils import text_iterator

    from pyltp import Postagger

    lm = load_lm('../jiayan_no_ws.klm')
    tokenizer = CharHMMTokenizer(lm)

    postagger = Postagger()
    postagger.load('/Users/jiaeyan/Desktop/ltp_data_v3.4.0/pos.model')

    data_file = '/Users/jiaeyan/Desktop/chn_data/all.txt'
    # with open('/Users/jiaeyan/Desktop/chn_data/pos_all.txt', 'w') as f:
    #     for line in text_iterator(data_file):
    #         words = list(tokenizer.tokenize(line))
    #         postags = list(postagger.postag(words))
    #         f.write(' '.join(words) + '\t' + ' '.join(postags) + '\n')
    with open(data_file, 'r') as in_f, \
        open('/Users/jiaeyan/Desktop/chn_data/pos_all.txt', 'w') as out_f:
        for line in in_f:
            for seg in line.strip().split():
                if seg:
                    words = list(tokenizer.tokenize(seg))
                    postags = list(postagger.postag(words))
                    out_f.write(' '.join(words) + '\t' + ' '.join(postags) + '\n')

            # line = line.strip()
            # if line:
            #     words = list(tokenizer.tokenize(line))
            #     postags = list(postagger.postag(words))
            #     out_f.write(' '.join(words) + '\t' + ' '.join(postags) + '\n')

    postagger.release()


def gen_dict():
    from collections import Counter
    from jiayan import load_lm
    from jiayan import CharHMMTokenizer
    from jiayan.utils import text_iterator

    lm = load_lm('../jiayan_no_ws.klm')
    tokenizer = CharHMMTokenizer(lm)

    data_file = '/Users/jiaeyan/Desktop/chn_data/all.txt'

    words = []

    for line in text_iterator(data_file):
        words.extend({word for word in list(tokenizer.tokenize(line)) if len(word) > 1})
    d = Counter(words)

    for word in d:
        mutuals = ((get_pmi(lm, word, i), i) for i in range(len(word) - 1))
        pmi = min(mutuals)
        d[word] = (d[word], pmi[0], pmi[1])

    words = sorted(d, key=lambda x: (len(x), -d[x][0], -d[x][1]))
    with open('/Users/jiaeyan/Desktop/chn_data/dict.txt', 'w') as out_f:
        for word in words:
            freq, pmi, idx = d[word]
            out_f.write('{}: {} {} {}\n'.format(word, freq, pmi, idx))


def get_pmi(lm, seg, i):
    pmi = lm.score(' '.join(seg), eos=False, bos=False) - \
          (lm.score(' '.join(seg[:i+1]), eos=False, bos=False) + lm.score(' '.join(seg[i+1:]), eos=False, bos=False))
    return pmi


if __name__ == '__main__':
    # def rd():
    #     return 0.3
    # # random.seed(41)
    # a = [1, 2, 3, 7, 9]
    # b = [4, 5, 6, 8, 0]
    # random.shuffle(a, rd)
    # random.shuffle(b, rd)
    # print(a)
    # print(b)
    # a = [1, 4, 2, 6, 9]
    # b = sorted(a)
    # print(b)
    # from pyltp import Segmentor
    # #
    # segmentor = Segmentor()
    # segmentor.load("/Users/jiaeyan/Desktop/ltp_data_v3.4.0/cws.model")
    # words = segmentor.segment('是故内圣外王之道，暗而不明，郁而不发，天下之人各为其所欲焉以自为方。')
    # print(list(words))
    #
    # from pyltp import Postagger
    #
    # words = ['是', '故', '内圣外王', '之', '道', '，', '暗', '而', '不', '明', '，', '郁', '而', '不', '发', '，', '天下', '之', '人', '各', '为', '其', '所', '欲', '焉', '以', '自', '为', '方', '。']
    # postagger = Postagger()  # 初始化实例
    # postagger.load('/Users/jiaeyan/Desktop/ltp_data_v3.4.0/pos.model')  # 加载模型
    # postags = postagger.postag(words)  # 词性标注
    # print(list(postags))
    #
    # segmentor.release()
    # postagger.release()  # 释放模型
    # pos_train()
    gen_dict()


