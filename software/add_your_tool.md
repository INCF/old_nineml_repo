---
layout: article
title: "Add Your Tool To the Software Gallery"
excerpt: "Add your tool to the gallery"
image:
  feature:
  teaser:
  thumb:
toc: false
share: false
ads: false
---

In order to add your software tool the the 9ML software gallery please

1. fork the [9ML repository on GitHub (http://github.com/INCF/nineml)](http://github.com/INCF/nineml)
1. checkout the 'gh-pages' branch
1. copy the yaml markdown template at the bottom of the page into a new file replacing the text in between `<>` with the relevant information for your tool
1. save the markdown file to path `<git-repo>/_posts/software/0001-01-01-<name-of-your-tool>.md`
1. copy the feature and teaser images to the `images` directory
1. [add](http://git-scm.com/docs/git-add), [commit](http://git-scm.com/docs/git-commit) and [push](http://git-scm.com/docs/git-push) your changes to your GitHub fork
1. open a [pull request](https://help.github.com/articles/using-pull-requests/) into the `INCF:gh-pages` branch (<b><u>not</u></b> the default `INCF:master` branch)
1. wait for us to merge your pull request.

#####YAML template

{% highlight yaml %}
---
layout: article
title: "<name-of-your-tool>"
excerpt: "<brief-summary-of-your-tool>"
image:
  feature: <name-of-your-tool>-feature.png  # ~1500x250px "banner" for the top of your page (can be any web-image type)
  teaser:  <name-of-your-tool>-teaser.png   # 400x250px "teaser" imagae for the gallery (can be any web-image type)
  thumb:
toc: false
share: false
ads: false
---

<Description of your tool and the level of 9ML support it currently has>
{% endhighlight %}