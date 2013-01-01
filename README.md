XX Books
===============

by Andriy


## What's this?

This is my Graduation Project -- *A Personal Book Info Management & Recommendation System Based on Collaborative Filtering and Tag System*.


## Platforms

* Web: GAE + GWT

* Mobile: Android, iOS (probably), WP (probably)


## Functionality

* Account & Log in

	- Use Douban account to log in

	- Set preferences when log in for the first time

	- Can bind the Tongji Library account

	- Can set the goals of reading recently (system will notify if that is unrealistic)

* Book information source

	- Mainly from Douban

	- Also from Amazon if it's non-Chinese

	- Also from Tongji Library if user has binded his account

	- Also import the history data from user's account in Tongji Library

	- Provide link for searching in ishare

	- Upload from user (e-book)

	- Manually entered if none of above works

	- Simple format conversion (e.g. HTML 2 txt)

* Book management

	- Can choose to sync all operations to Douban

	- Can make a tag, comment, rate a book (5-point scale)

	- One book could be *read*, *reading*, *borrowable*, *borrowed*, *expired*, *buyable*, *bought*
		
		+ For *borrowable*, *borrowed*, *expired* books, get their information in Tongji Library automatically

		+ For *buyable* books, provide links in Taobao, Dangdang, Amazon.cn, Amazon, 360buy, ishare, etc.

	- Can new, delete, copy a book list

	- Can search within book lists with filters

	- Can add books to book lists

	- Can tag a book list

	- Sort a book list in following ways (at least)

		+ Ratings from Douban, Amazon, etc.

		+ Amount of people that have rated

		+ Word count

		+ Tag

		+ The lowest price online (if a free e-book is available, make it zero)

		+ Random

	- Can share a book list with a link (No sign-in required)

* Statistics & recommendation

	- Display how many books, what kind of books user have read during a period

	- Can display via a table or a graph

	- Can recommend a book for next reading, according to: (customizable)

		+ Reading history of user

		+ User preference

		+ Tag

		+ Recent reading goals

	- Present reasons for recommendation

	- Customizable means user can change some coefficients of the algorithm

	- Can also recommend those not in user's book lists

	- Recommend by Collaborative filtering algorithms and tag system
