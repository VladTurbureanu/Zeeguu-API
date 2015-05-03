CREATE TABLE words
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
word varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL UNIQUE
);


INSERT INTO words (word)
SELECT DISTINCT word
FROM word;




CREATE TABLE word_ranks
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
word_id INT NOT NULL,
language_id VARCHAR(2) NOT NULL,
rank INT NOT NULL,
FOREIGN KEY (word_id) REFERENCES words(id),
FOREIGN KEY (language_id) REFERENCES language(id),
CONSTRAINT uc_wordID UNIQUE (word_id,language_id)
);

CREATE TABLE user_words
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
language_id VARCHAR(2) NOT NULL,
word_id INT NOT NULL,
rank_id INT,
FOREIGN KEY (word_id) REFERENCES words(id),
FOREIGN KEY (language_id) REFERENCES language(id),
FOREIGN KEY (rank_id) REFERENCES word_ranks(id),
CONSTRAINT uc_wordID UNIQUE (word_id,language_id)
)