CREATE TABLE exercise_based_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
user_words_id INT NOT NULL,
probability DECIMAL NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (user_words_id) REFERENCES user_words(id),
CONSTRAINT uc_exercise_prob UNIQUE (user_id,user_words_id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)
);

CREATE TABLE encounter_based_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
word_ranks_id INT NOT NULL,
count_not_looked_up INT NOT NULL,
probability DECIMAL NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (word_ranks_id) REFERENCES word_ranks(id),
CONSTRAINT uc_exercise_prob UNIQUE (user_id,word_ranks_id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)

);

CREATE TABLE aggregated_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
user_words_id INT,
word_ranks_id INT,
probability DECIMAL NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (user_words_id) REFERENCES user_words(id),
FOREIGN KEY (word_ranks_id) REFERENCES word_ranks(id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)
);
