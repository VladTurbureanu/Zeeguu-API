ALTER TABLE word_rank
DROP INDEX uc_wordID,
ADD CONSTRAINT wr_word UNIQUE (word,language_id);

ALTER TABLE user_word
DROP INDEX uc_wordID,
ADD CONSTRAINT uw_word UNIQUE (word,language_id)