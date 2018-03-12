import praw
from praw.models import MoreComments
import re
from collections import defaultdict
import io
from datetime import datetime, timedelta
import pprint
import date_converter
import unicodecsv as csv
import plac


reddit = praw.Reddit(client_id='1bxPsJDD2lZodg',
                     client_secret='8H-rpDtGeQIo9uj3SBupW2SNUfA',
                     password='redditLunt1k!!',
                     user_agent='testscript by /u/verasazonova',
                     username='verasazonova')

print(reddit.user.me())


def get_tag_text(title):
	p = re.compile(r"\[([\w\s]+)\]", flags=re.UNICODE|re.IGNORECASE)
	tags = [m.group(1).lower().replace(" ", "_") for m in p.finditer(title)]
	text = re.sub(p, "", title)
	return tags, text


def get_subredit(subreddit, from_timestamp, to_timestamp):
	params = {'sort':'new', 'limit':None, 'syntax':'cloudsearch'}
	timstr = 'timestamp:{0}..{1}'.format(int(from_timestamp), int(to_timestamp))
	print(timstr)
	return reddit.subreddit(subreddit).search(timstr, **params)

@plac.annotations(
    from_timestamp=("From timestamp", "option", "f", int),
    to_timestamp=("To timestamp", "option", "t", int)
)
def main(from_timestamp=None, to_timestamp=None):
	if to_timestamp is None:
		to_date = datetime.now()
		to_timestamp = date_converter.date_to_timestamp(to_date)
	if from_timestamp is None:
		from_date = to_date - timedelta(days=1095)
		from_timestamp = date_converter.date_to_timestamp(from_date)
	oldest = to_timestamp

	print(from_timestamp, to_timestamp)
	subreddits = get_subredit('SkincareAddiction', from_timestamp, to_timestamp)
	total = 0
	total_comments = 0
	batch = 0
	had_submissions = True
	with open('submissions.csv', 'a') as f:
		w = csv.writer(f, encoding='utf-8')
		header = map(unicode, ["id", "created", "title", "text", "subredit", "tags", "type", "parent_id"])
		w.writerow(header)
		while oldest > from_timestamp and had_submissions:
			for i, submission in enumerate(subreddits):
				created = submission.created
				tags, title = get_tag_text(submission.title)
				text = submission.selftext
				id_ = submission.id
				subred = submission.subreddit_name_prefixed

				if created < oldest:
					oldest = created
				row = map(unicode, [id_, created, title, text, subred, "|".join(tags), "submission", ""])
				w.writerow(row)

				submission.comments.replace_more(limit=None)
				for comment in submission.comments.list():
					created = comment.created
					text = comment.body
					id_ = comment.id
					subred = comment.subreddit_name_prefixed
					parent_id = comment.parent_id
					row = map(unicode, [id_, created, "", text, subred, "|".join(tags), "comment", parent_id])
					w.writerow(row)
					total_comments += 1
			
			had_submissions = (i != 0)
			print("batch {} done. got {} submissions oldest is at {}. getting another batch".format(batch, i, oldest))
			batch += 1
			total += i
			subreddits = get_subredit('SkincareAddiction', from_timestamp, oldest)

	print("No submissions in the last batch? {}".format(had_submissions))

	print("Processed {} batches with {} submissions and {} comments going back to {}".format(
		batch, total, total_comments, oldest))

	# print(submission.selftext)
	# print(submission.title)
	# pprint.pprint(vars(submission))
	# print("")

def test_re():

	print()
	print(get_tag_text("[Product Question] If you use Stratia's Liquid Gold, do you use other moisturizers - what are they?"))
	print(get_tag_text("[Skin_concerns][routine_help] I don't know what to do"))
	print(get_tag_text("I've got some conerns [skin_concerns]"))
	print(get_tag_text("[skin_concerns] blah some more text"))


if __name__ == "__main__":
	#test_re()
	plac.call(main)


