DROP TABLE IF EXISTS contribution_event_exercise_learning,contribution_event,event_source,event_outcome;

CREATE TABLE event_outcome
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
outcome varchar(255) NOT NULL,
UNIQUE KEY `outcome_UNIQUE` (`outcome`)
);

CREATE TABLE event_source
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
source varchar(255) NOT NULL,
UNIQUE KEY `source_UNIQUE` (`source`)
);

insert into event_outcome (id, outcome) values (1, 'Do not know');
insert into event_outcome (id, outcome) values (2, 'Retry');
insert into event_outcome (id, outcome) values (3, 'Correct');
insert into event_outcome (id, outcome) values (4, 'Wrong');
insert into event_outcome (id, outcome) values (5, 'Typo');

insert into event_source (id, source) values (1, 'Recognize');
insert into event_source (id, source) values (2, 'Translate');

CREATE TABLE contribution_event
(
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
outcome varchar(255) NOT NULL,
source varchar(255) NOT NULL,
FOREIGN KEY (outcome) REFERENCES EVENT_OUTCOME(outcome),
FOREIGN KEY (source) REFERENCES EVENT_SOURCE(source),
speedMilliSec INT,
time DATETIME NOT NULL
);


CREATE TABLE contribution_event_exercise_learning
(
contribution_event_id INT NOT NULL,
contribution_id INT NOT NULL,
FOREIGN KEY (contribution_event_id) REFERENCES CONTRIBUTION_EVENT(id),
FOREIGN KEY (contribution_id) REFERENCES CONTRIBUTION(id)
);




