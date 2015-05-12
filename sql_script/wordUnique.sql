ALTER TABLE word_ranks
DROP INDEX uc_wordID,
ADD CONSTRAINT wr_word UNIQUE (word,language_id);

ALTER TABLE user_words
DROP INDEX uc_wordID,
ADD CONSTRAINT uw_word UNIQUE (word,language_id)