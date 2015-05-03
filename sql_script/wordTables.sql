INSERT INTO user_words (id, language_id, word_id, rank_id)
SELECT  word.id , word.language_id ,words.id, null 
FROM    word, words
WHERE   words.id NOT IN
        (
        SELECT  word_id
        FROM    word_ranks
        ) 
        AND word.word = words.word 
UNION
SELECT word.id ,  word.language_id ,words.id , null 
FROM    word, words
WHERE word.language_id <> 'de'AND word.word = words.word

UNION
SELECT  word.id , word.language_id,words.id, word_ranks.id
FROM    word, words, word_ranks
WHERE   words.id IN
        (
        SELECT  word_id
        FROM    word_ranks
        ) 
        AND word.word = words.word 
        AND word_ranks.word_id = words.id
        AND word.language_id = 'de'







