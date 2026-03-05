

查询表
create table Query(
    id      ,
    url     ,
    title   ,
    uuid     
)
    id唯一标识    int主键
    url前端申请查询的新闻连接  varchar
    title前端申请查询的新闻    varchar
    uuid全局唯一标识符，用来供前端查询使用


create table Result(
    id       ,
    title    ，
    truth    ,
    content  ,
    knowledge,
    query_id
)
补充：
    id唯一标识  int主键
    title用户查询的新闻，也是去系统里跑的新闻  varchar
    truth新闻真假判断  bool型
    content就是证据链的内容  varchar
    knowledge是可视化的rag的图片
    query_id对应上面的query表的id，int外键关联query表的id,

result对cite是一对多的关系，因为cite是证据链当中的相关新闻证据

create table Cite(
    id       ,
    url      ,
    title    ,
    relevance,
    newstime ,
    result_id
)
补充：
    result_id对应Result表当中的id，是外键，与其是一对多的关系，及一个Result表的id对应多个cite表的id int
    url是相关新闻的url varchar
    title是（input里面）相关新闻的标题 varchar
    relevance是相关度 int
    newtime新闻发布时间 varchar（暂时）
    id唯一标识 int

补充：
现在的问题是，什么时候把跑出来的数据从缓存存储到数据库，和什么时候从数据库当中读取这个数据
初步设想是，在跑主函数的时候，最后的地方加上从result的证据链得最后返回，所以内容最后一起返回给前端


其实cite表里的内容都是brave search跑出来的相关信息，可以在第一步获取rag的时候直接插入到cite表，但是他和result表的对应关系（那就先插入已经知道的result表内容，让他对应），cite表需要新闻的date，得修改爬取时候的代码，把时间也爬取。

* 补充： 
       现在的问题是，什么时候把跑出来的数据从缓存存储到数据库，和什么时候从数据库当中读取这个数据 初步设想是，在跑主函数的时候，最后的地方加上从result的证据链得最后返回，所以内容最后一起返回给前端
       其实cite表里的内容都是brave search跑出来的相关信息，可以在第一步获取rag的时候直接插入到cite表，但是他和result表的对应关系（那就先插入已经知道的result表内容，让他对应），cite表需要新闻的date，得修改爬取时候的代码，把时间也爬取。