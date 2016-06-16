import json
import datetime

current_year = datetime.date.today().year
current_month = datetime.date.today().month
current_day = datetime.date.today().day
days_in_month = 31


# return true if learned or false if not
# implement that outcome too easy includes before date
# before_date is not used yet, but it will be needed later for implementing more precision in calculations
def is_bookmark_word_learned(bookmark, before_date):
    return bookmark.check_is_latest_outcome_too_easy()


# calculate totals before the date which is 1 year ago
def compute_learner_stats_before(user):
    learned = 0
    learning = 0

    before_date = datetime.datetime(current_year - 1, current_month, current_day)
    all_bookmarks = user.all_bookmarks(before_date=before_date)

    for bookmark in all_bookmarks:
        learned = is_bookmark_word_learned(bookmark, before_date)
        if learned:
            learned += 1
        else:
            learning += 1

    return [learned, learning]


# compute learned and learning words per month after the given date which is 1 year ago
# compute_learner_stats_during_last_year
def compute_learner_stats_after(user, learner_stats_before):
    # array of months , each month will hold amount of number learned/learning words
    learning_stats_after = [0] * 12
    learned_stats_after = [learner_stats_before[0]] * 12

    after_date = datetime.datetime(current_year - 1, current_month, current_day)
    all_bookmarks_after_date = user.all_bookmarks(after_date)

    for bookmark in all_bookmarks_after_date:
        # bookmark.time needs to return the month number
        current_bookmark_month = int(bookmark.time.strftime("%m"))
        index = (current_bookmark_month - current_month) % 12

        learned = is_bookmark_word_learned(bookmark, datetime.datetime(current_year, index + 1, days_in_month))
        if learned:
            learned_stats_after[index] += 1
        else:
            learning_stats_after[index] += 1
    #learned_stats_after[10] = 27;  # for testing purpose
    for i in range(0, 12):
        learning_stats_after[i] += learning_stats_after[max(0, (i - 1))] + (learner_stats_before[1] - learned_stats_after[i])

    # uncomment below 2 lines to show total learned each month, but not only per month
    #for i in range(1, 12):
    #    learned_stats_after[i] += learned_stats_after[i-1]

    return [learning_stats_after, learned_stats_after]


def data_to_json(learner_stats_after):
    #      "Status": "Learning",
    #      "words": "202",
    #      "date": "Jan 2016"
    learning_stats_after = learner_stats_after[0]
    learned_stats_after = learner_stats_after[1]

    result = ""
    for i in range(0, 12):
        entry_year = current_year
        if current_month > i:
            entry_year -= 1
        entry_month = (current_month + i) % 12 + 1
        entry_date = datetime.datetime(entry_year, entry_month, 1)
        entry_date = str(entry_date.strftime("%b %Y"))
        result = result + "{\"Status\": \"Learning\", \"words\": \"" + str(learning_stats_after[i]) + "\", \"date\": \"" + entry_date + "\"},"
        result = result + "{\"Status\": \"Learned\", \"words\": \"" + str(learned_stats_after[i]) + "\", \"date\": \"" + entry_date + "\"},"

    result = "[" + result[:-1] + "]"
    return json.dumps(result)


def compute_learner_stats(user):
    # first compute before the given date
    learner_stats_before = compute_learner_stats_before(user)
    # start computing per month after the given date
    learner_stats_after = compute_learner_stats_after(user, learner_stats_before)
    # return the result array as json
    return data_to_json(learner_stats_after)
