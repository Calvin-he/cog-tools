""" merge pronounciations from multiple words
"""
import os
import sys
import random
import datetime
import time
from pymongo import MongoClient
from pydub import AudioSegment

MEDIA_DIR = '/home/www/cog/public/media/'
MODULE_DIR = os.path.dirname(os.path.realpath(__file__))
COCA_DIRNAME = 'coca_audios'
DB = MongoClient('localhost', 27017)['ce']

progress_seq = 0

def read_progress():
    global progress_seq
    filepath = os.path.join(MEDIA_DIR, COCA_DIRNAME, '.progress_seq')
    if os.path.exists(filepath):
        with open(filepath, 'r') as progressf:
            progress_seq = int(progressf.read())

def write_progress():
    global progress_seq
    filepath = os.path.join(MEDIA_DIR, COCA_DIRNAME, '.progress_seq')
    with open(filepath, 'w') as progressf:
        progressf.write(str(progress_seq))


def get_wordlist(file_path):
    """ get a list of all words
    """
    words_list = []
    with open(file_path) as word_file:
        for line in word_file:
            if line.strip():
                words_list.append(line.strip())
    return words_list

def merge_wordlist(words, export_filename):
    """ merge pronounciation of words
    """
    cursor = DB.words.find({'word': {'$in': words}})
    # order words by original ordering
    ordered_words = [w for w in cursor]
    for wp in ordered_words:
        idx = words.index(wp['word'])
        wp['seq'] = idx
    ordered_words.sort(key=lambda x: x['seq'])
    pronuns = []
    for wp in ordered_words:
        if not wp['_forvoResults']:
            raise Exception('No pronouciations for Word ' + wp['word'])

        wp_pronuns = wp['pronouns']
        if wp_pronuns:
            pronuns.append(wp_pronuns[0])
            pronuns.append(wp_pronuns[1 % len(wp_pronuns)])
            pronuns.append(wp_pronuns[2 % len(wp_pronuns)])
    if not pronuns:
        return

    audios =  AudioSegment.empty()
    for p in pronuns:
        audio_path = p['audioPath'].replace('/media', MEDIA_DIR, 1)
        audios += AudioSegment.from_file(audio_path, format='mp3')
    
    export_path = os.path.join(MEDIA_DIR, COCA_DIRNAME, export_filename)
    audios.export(export_path, format='mp3')

    now = datetime.datetime.utcnow()
    DB.media.insert_one({
        'path': os.path.join('/media', COCA_DIRNAME, export_filename),
        'created': now,
        'updated': now,
        '__v': 0
    })
    write_progress()

def run():
    """ main function
    """
    global progress_seq
    word_list = get_wordlist(os.path.join(MODULE_DIR, 'coca_words.txt'))
    read_progress()
    for i in xrange(progress_seq, len(word_list), 10):
        end = (i+10) if (i+10) < len(word_list) else len(word_list)
        cur_wordlist = word_list[i:end]
        export_filename = 'COCAIII_%04d-%04d.mp3' % (i+1, end)
        print 'proccessing to merge %s' % export_filename
        progress_seq += end - i
        merge_wordlist(cur_wordlist, export_filename)

def clean():
    """ clean
    """
    pattern = '^/media/coca_audios/.*$'
    for media in DB.media.find({'path': {'$regex': pattern}}):
        if media['path'].startswith('/media/coca_audios/'):
            DB.media.delete_one({'_id': media['_id']})
        else:
            print media['path']
    cocadir = os.path.join(MEDIA_DIR, COCA_DIRNAME)
    for filename in os.listdir(cocadir):
        os.remove(os.path.join(cocadir, filename))

if __name__ == '__main__':
    if sys.argv[1] == 'run':
        run()
    if sys.argv[1] == 'clean':
        clean()
