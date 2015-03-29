DROP TABLE IF EXISTS bookmark_translation_mapping

CREATE TABLE bookmark_translation_mapping
(
bookmark_id INT NOT NULL,
translation_id INT NOT NULL,
FOREIGN KEY (bookmark_id) REFERENCES contribution(id),
FOREIGN KEY (translation_id) REFERENCES word(id)
);