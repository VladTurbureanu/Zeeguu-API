DROP TABLE IF EXISTS contribution_learning_event_mapping,learning_event,event_source,event_outcome;

CREATE TABLE event_outcome
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
outcome varchar(255) NOT NULL
);

CREATE TABLE event_source
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
source varchar(255) NOT NULL
);

insert into event_outcome (id, outcome) values (1, 'Do not know');
insert into event_outcome (id, outcome) values (2, 'Retry');
insert into event_outcome (id, outcome) values (3, 'Correct');
insert into event_outcome (id, outcome) values (4, 'Wrong');
insert into event_outcome (id, outcome) values (5, 'Typo');
insert into event_outcome (id, outcome) values (6, 'I know');


insert into event_source (id, source) values (1, 'Recognize');
insert into event_source (id, source) values (2, 'Translate');

CREATE TABLE learning_event
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
event_source_id INT NOT NULL,
event_outcome_id INT NOT NULL,
FOREIGN KEY (event_outcome_id) REFERENCES EVENT_OUTCOME(id),
FOREIGN KEY (event_source_id) REFERENCES EVENT_SOURCE(id),
speedMilliSec INT,
time DATETIME NOT NULL
);


CREATE TABLE contribution_learning_event_mapping
(
learning_event_id INT NOT NULL,
contribution_id INT NOT NULL,
FOREIGN KEY (learning_event_id) REFERENCES LEARNING_EVENT(id),
FOREIGN KEY (contribution_id) REFERENCES CONTRIBUTION(id)
);




