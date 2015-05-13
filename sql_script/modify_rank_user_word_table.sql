
ALTER TABLE word_ranks
ADD word VARCHAR(255) NOT NULL ,
DROP FOREIGN KEY word_ranks_ibfk_3;

ALTER TABLE user_words
ADD word VARCHAR(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
DROP FOREIGN KEY user_words_ibfk_8;

SET SQL_SAFE_UPDATES=0;

UPDATE words w, word_ranks r
SET r.word = lower(w.word)
WHERE r.word_id = w.id;

UPDATE words w, user_words u
SET u.word = w.word
WHERE u.word_id = w.id;

SET SQL_SAFE_UPDATES=1;

ALTER TABLE word_ranks
DROP INDEX uc_wordID,
ADD CONSTRAINT wr_wordID UNIQUE (word,language_id);

ALTER TABLE user_words
DROP INDEX uc_word,
ADD CONSTRAINT uw_word UNIQUE (word,language_id)