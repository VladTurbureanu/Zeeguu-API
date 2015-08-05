CREATE TABLE exercise_based_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
user_word_id INT NOT NULL,
probability DECIMAL(10,9) NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (user_word_id) REFERENCES user_word(id),
CONSTRAINT uc_exercise_prob UNIQUE (user_id,user_word_id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)
);

CREATE TABLE encounter_based_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
word_rank_id INT NOT NULL,
count_not_looked_up INT NOT NULL,
probability DECIMAL(10,9) NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (word_rank_id) REFERENCES word_rank(id),
CONSTRAINT uc_exercise_prob UNIQUE (user_id,word_rank_id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)

);

CREATE TABLE aggregated_probability
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
user_id INT NOT NULL,
user_word_id INT,
word_rank_id INT,
probability DECIMAL (10,9) NOT NULL,
FOREIGN KEY (user_id) REFERENCES user(id),
FOREIGN KEY (user_word_id) REFERENCES user_word(id),
FOREIGN KEY (word_rank_id) REFERENCES word_rank(id),
CONSTRAINT chk_probability CHECK (probability>=0 AND probability <=1)
);
