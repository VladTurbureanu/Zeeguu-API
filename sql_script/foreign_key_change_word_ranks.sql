DROP TABLE IF EXISTS words;

ALTER TABLE word_ranks
RENAME TO word_rank;

ALTER TABLE user_words
RENAME TO user_word;


