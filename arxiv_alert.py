import datetime
import requests
import json
import arxiv
import datetime
import pytz

subscribe_subject = ["AI", "CL", "CV", "IR", "LG", "MM", "SI"]
subscribe_subject_code = ["cat:cs." + subject for subject in subscribe_subject]

subscribe_authors = []

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"

time_now = datetime.datetime.now()
period_start_time = datetime.datetime(time_now.year, time_now.month, time_now.day - 3, 0, tzinfo=pytz.timezone("UTC"))


def get_the_paper_today(query, max_results=200):
    search_engine = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    today_papers = []
    for item in search_engine.results():
        published_date = item.published
        if published_date < period_start_time:
            break
        today_papers.append(item)
    return today_papers


def get_authors(authors, first_author=False):
    if not first_author:
        output = ", ".join(str(author) for author in authors)
    else:
        output = authors[0]
    return output


def sort_papers(papers):
    output = dict()
    keys = list(papers.keys())
    keys.sort(reverse=True)
    for key in keys:
        output[key] = papers[key]
    return output


def get_daily_papers(query, max_results=2):
    """
    @param max_results:
    @param topic: str
    @param query: str
    @return paper_with_code: dict
    """

    # output 
    content = dict()
    content_to_web = dict()

    # content
    today_papers = get_the_paper_today(query)

    cnt = 0

    for result in today_papers:

        paper_id = result.get_short_id()
        paper_title = result.title
        paper_url = result.entry_id
        code_url = base_url + paper_id
        paper_abstract = result.summary.replace("\n", " ")
        paper_authors = get_authors(result.authors)
        paper_first_author = get_authors(result.authors, first_author=True)
        primary_category = result.primary_category
        publish_time = result.published.date()
        update_time = result.updated.date()
        comments = result.comment

        print("Time = ", update_time,
              " title = ", paper_title,
              " author = ", paper_first_author)

        # eg: 2108.09112v1 -> 2108.09112
        ver_pos = paper_id.find('v')
        if ver_pos == -1:
            paper_key = paper_id
        else:
            paper_key = paper_id[0:ver_pos]

        try:
            r = requests.get(code_url).json()
            # source code link
            if "official" in r and r["official"]:
                cnt += 1
                repo_url = r["official"]["url"]
                content[paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|**[link]({repo_url})**|\n"
                content_to_web[paper_key] = f"- {update_time}, **{paper_title}**, {paper_first_author} et.al., Paper: [{paper_url}]({paper_url}), Code: **[{repo_url}]({repo_url})**"

            else:
                content[paper_key] = f"|**{update_time}**|**{paper_title}**|{paper_first_author} et.al.|[{paper_id}]({paper_url})|null|\n"
                content_to_web[paper_key] = f"- {update_time}, **{paper_title}**, {paper_first_author} et.al., Paper: [{paper_url}]({paper_url})"

            # TODO: select useful comments
            comments = None
            if comments is not None:
                content_to_web[paper_key] = content_to_web[paper_key] + f", {comments}\n"
            else:
                content_to_web[paper_key] = content_to_web[paper_key] + f"\n"

        except Exception as e:
            print(f"exception: {e} with id: {paper_key}")

    data = {query: content}
    data_web = {query: content_to_web}
    return data, data_web


def update_json_file(filename, data_all):
    with open(filename, "r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)

    json_data = m.copy()

    # update papers in each keywords         
    for data in data_all:
        for keyword in data.keys():
            papers = data[keyword]

            if keyword in json_data.keys():
                json_data[keyword].update(papers)
            else:
                json_data[keyword] = papers

    with open(filename, "w") as f:
        json.dump(json_data, f)


def json_to_md(filename, md_filename, to_web=False, use_title=True):
    """
    @param use_title:
    @param to_web:
    @param filename: str
    @param md_filename: str
    @return None
    """

    date_now = datetime.date.today()
    date_now = str(date_now)
    date_now = date_now.replace('-', '.')

    with open(filename, "r") as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    # clean README.md if daily already exist else create it
    with open(md_filename, "w+") as f:
        pass

    # write data into README.md
    with open(md_filename, "a+") as f:

        if use_title and to_web:
            f.write("---\n" + "layout: default\n" + "---\n\n")

        if use_title:
            f.write("## Updated on " + date_now + "\n\n")
        else:
            f.write("> Updated on " + date_now + "\n\n")

        for keyword in data.keys():
            day_content = data[keyword]
            if not day_content:
                continue
            # the head of each part
            f.write(f"## {keyword}\n\n")

            if use_title:
                if not to_web:
                    f.write("|Publish Date|Title|Authors|PDF|Code|\n" + "|---|---|---|---|---|\n")
                else:
                    f.write("| Publish Date | Title | Authors | PDF | Code |\n")
                    f.write("|:---------|:-----------------------|:---------|:------|:------|\n")

            # sort papers by date
            day_content = sort_papers(day_content)

            for _, v in day_content.items():
                if v is not None:
                    f.write(v)

            f.write(f"\n")

    print("finished")


if __name__ == "__main__":

    data_collector = []
    data_collector_web = []

    # keywords = dict()
    # keywords["SLAM"] = "SLAM"
    # keywords["SFM"] = "SFM" + "OR" + "\"Structure from Motion\""
    # keywords["Visual Localization"] = "\"Camera Localization\"OR\"Visual Localization\"OR\"Camera Re-localisation\""
    # keywords["Keypoint Detection"] = "\"Keypoint Detection\"OR\"Feature Descriptor\""
    # keywords["Image Matching"] = "\"Image Matching\""

    # for topic, keyword in keywords.items():
    for subject_code in subscribe_subject_code:
        # topic = keyword.replace("\"","")
        data, data_web = get_daily_papers(query=subject_code, max_results=10)
        data_collector.append(data)
        data_collector_web.append(data_web)

    # 1. update README.md file
    json_file = "cv-arxiv-daily.json"
    md_file = "README.md"
    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file, md_file)

    # 2. update docs/index.md file
    json_file = "./docs/cv-arxiv-daily-web.json"
    md_file = "./docs/index.md"
    # update json data
    update_json_file(json_file, data_collector)
    # json data to markdown
    json_to_md(json_file, md_file, to_web=True)

    # 3. Update docs/wechat.md file
    json_file = "./docs/cv-arxiv-daily-wechat.json"
    md_file = "./docs/wechat.md"
    # update json data
    update_json_file(json_file, data_collector_web)
    # json data to markdown
    json_to_md(json_file, md_file, to_web=False, use_title=False)
