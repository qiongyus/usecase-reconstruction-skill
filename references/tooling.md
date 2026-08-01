# tooling.md — 按语言的取证工具

Step 3（系统操作清单）与 Step 4（聚合成用例）需要按语言提取入口点、导出符号与测试。`scripts/inventory_entrypoints.sh` 已用跨语言 grep 覆盖了 HTTP 路由 / CLI 子命令 / 消息消费者 / 定时任务 / RPC 方法的通用模式；本文补充语言专属的更精确手段，以及调用图与测试发现工具。**先 `--version` 跑通再依赖它**——不保证下列工具在你读到时仍活跃维护。

## Go

| 用途 | 手段 |
|---|---|
| 路由提取 | grep 框架特征：`net/http` 标准库 `mux.Handle(`/`case "/...":`，`gorilla/mux` 的 `.HandleFunc(`，`gin` 的 `r.GET(`/`r.POST(`，`echo` 的 `e.GET(`；`inventory_entrypoints.sh` 已覆盖这几种 |
| 导出符号 | 首字母大写即导出，`grep -n '^func [A-Z]'` 或更准确地用 `go doc -all ./...` 逐包列出 |
| 调用图 | `go-callvis`（单个函数的可视化调用图，产出 SVG）；`golang.org/x/tools/cmd/callgraph`（命令行，输出完整调用边） |
| 测试发现 | `go test -list '.*' ./...` 列出全部测试函数名；e2e/集成测试常见 `//go:build e2e` 构建标签，用 `go list -tags e2e ./...` 单独枚举 |

## Java

| 用途 | 手段 |
|---|---|
| 路由提取 | grep `@RequestMapping`/`@GetMapping`/`@PostMapping`（Spring）、`@Path`（JAX-RS） |
| 导出符号 | `public class` 上的 `public` 方法即 API 面；对编译产物用 `javap -public <class>` 逐类列出，比源码 grep 更准确（能跳过被注释掉的代码） |
| 调用图 | `java-callgraph`（gousiosg，静态/动态两种模式生成调用图）；无第三方依赖时可用 IDE 的 "Call Hierarchy" 手动核实关键路径 |
| 测试发现 | Maven：`mvn test -Dtest=ClassName#method -DskipTests=false` 前先 `mvn test -Denforcer.skip=true -DskipTests` 走一遍收集列表；e2e/集成测试惯例用独立命名（Failsafe 插件的 `*IT.java`）与单元测试（`*Test.java`）区分 |

## Python

| 用途 | 手段 |
|---|---|
| 路由提取 | grep `@app.route`（Flask）、`@app.get`/`@app.post`（FastAPI）、Django 的 `urlpatterns`/`path(` |
| 导出符号 | 有 `__all__` 列表时以其为准；无 `__all__` 时按惯例非下划线开头的顶层名皆视为公开，`python -c "import pkg, pprint; pprint.pprint(dir(pkg))"` 可枚举 |
| 调用图 | `pyan3`（静态调用图生成器，输出 dot）；`code2flow`（多语言支持，Python/JS/PHP/Ruby 通用） |
| 测试发现 | `pytest --collect-only -q` 列出全部用例而不执行；BDD 用 `behave --dry-run features/` 或 `pytest-bdd`；e2e 常见目录 `tests/e2e`、`tests/integration` |

## TypeScript / JavaScript

| 用途 | 手段 |
|---|---|
| 路由提取 | grep Express 的 `app.get(`/`app.post(`、NestJS 的 `@Controller()`/`@Get()`；Next.js 是文件路由，直接 `find pages/api app -name 'route.ts'` |
| 导出符号 | `export function`/`export const`/`export class` 逐个 grep；更系统的做法是跑 `tsc --declaration` 生成 `.d.ts` 或用 `api-extractor`（Microsoft Rush Stack）产出 API report，两者都能得到完整公开面而不必手工判断哪些是内部符号 |
| 调用图 | `madge`（依赖图，模块级而非函数级，但足以定位入口的下游影响面）；需要函数级调用关系时用 `ts-morph` 写一段 AST 遍历脚本 |
| 测试发现 | `jest --listTests`；e2e 框架 `playwright`/`cypress` 独立成 `e2e/` 目录（`*.spec.ts`/`*.cy.ts`）；BDD 用 `cucumber-js`（`.feature` 文件） |

## Rust

| 用途 | 手段 |
|---|---|
| 路由提取 | grep `actix-web` 的 `#[get("/path")]`/`#[post("/path")]`，`axum` 的 `Router::new().route(` |
| 导出符号 | `pub fn`/`pub struct`/`pub enum`；`cargo doc --no-deps` 生成的 rustdoc 是公共 API 全集；`cargo public-api` 可直接把公开面 diff 出来，比手动 grep 更不容易漏项 |
| 调用图 | `cargo-modules`（模块树与模块间依赖图，`cargo modules dependencies` 子命令） |
| 测试发现 | `cargo test -- --list`；Rust 惯例把集成测试放在顶层 `tests/` 目录（每个文件是独立 crate），与 `src/` 内的单元测试天然分开，无需额外约定即可区分 |

## Ruby

| 用途 | 手段 |
|---|---|
| 路由提取 | Rails 项目直接跑 `bin/rails routes`，比 grep `config/routes.rb` 的 DSL 更权威（会展开 `resources` 生成的全部子路由）；Sinatra 用 grep `get '/path' do`/`post '/path' do` |
| 导出符号 | Ruby 没有模块级导出声明，`public`/`private`/`protected` 是方法级可见性；`public_instance_methods(false)` 在 REPL 里可枚举某类自身定义的公开方法 |
| 调用图 | 静态工具较弱，`code2flow` 对 Ruby 有基本支持；更可靠的是跑 `rails runner` 配合 `TracePoint` 做一次性动态追踪 |
| 测试发现 | RSpec 用 `rspec --dry-run`；e2e 常见 `spec/features/`（Capybara）、`spec/system/`；BDD 用 `cucumber`（`.feature` 文件） |

## 为什么动态分析不在本 skill 的默认流程内

以下依据均来自 feature location 综述【一手】：Dit, Revelle, Gethers, Poshyvanyk. *Feature Location in Source Code: A Taxonomy and Survey*. Journal of Software Maintenance and Evolution: Research and Practice (JSME), 2013（系统性文献综述，覆盖 89 篇文章、25 个学术会议/期刊）。

**方向不匹配。** 该综述在摘要开篇即给出 feature location 的任务定义：

> Feature location is the activity of identifying an initial location in the source code that implements functionality in a software system.

综述正文进一步指出这个任务隐含的前提，用于把 feature location 与 aspect mining 等相邻领域区分开（§1 Introduction）：

> …in the contexts in which feature location is used, **the high-level descriptions of features are already known and only the code that implements them is unknown.**

这句话是要害：feature location 假定「功能是什么」已经知道，要找的是它在代码里的位置——方向与用例重建正相反。本 skill 要产出的正是那个「已知的功能描述」（用例目标），FL 技术本身不解决这个问题，最多能用来验证一个已经假设好的用例名在代码里对应哪些文件。

**动态分析要求先知道要找什么，且要能跑起来。** 综述在 §3.1 Type of Analysis 描述动态方法的通用流程：

> Feature location using dynamic analysis generally relies on a post-mortem analysis of an execution trace. Typically, **one or more feature-specific scenarios are developed that invoke only the desired feature.** Then, the scenarios are run and execution traces are collected…

设计这样的场景本身就要求分析者已经知道目标 feature 是什么，否则无从「只触发这一个功能」；综述随后也承认这一步在实践中很难做到：

> …it may be **difficult to formulate a scenario that invokes only the desired feature**, causing irrelevant code to be executed.

对用例重建而言，这构成循环依赖——设计场景需要先有用例假设，而用例假设正是待产出物，不能当作已知前提。此外动态分析要求系统可编译、可运行、可插桩，逆向重建常常拿不到这些条件（依赖缺失、需要种子数据、构建链本身已损坏）。

**静态与文本分析也不是免费的，但至少方向匹配且不需要运行系统。** 同一小节记录了两者的已知局限，取证时应据此调低预期而非无脑信任结果。静态分析：

> …it often **overestimates** what is pertinent to a feature and is prone to returning **many false positive results**.

文本分析（`inventory_entrypoints.sh` 的 grep 匹配本质上属于这一类）：

> …the quality of feature location is **heavily tied to the quality of the source code naming conventions** and/or the user-issued query.

命名规范差的代码库，本 skill 依赖 grep 的入口点提取会漏报或误报更多，需要人工复核补齐，这也是为什么各语言表都优先给"更准确的原生手段"（如 `go doc`、`javap -public`、`cargo public-api`）而不是无差别 grep。

动态分析并非完全排除在外——如果用户明确要做深度行为验证且系统可运行，跑一遍既有 e2e/集成测试并开启日志/tracing，能提供比静态推断更可靠的证据（见 `evidence-discipline.md` 四·2）。但这属于按需的补充验证手段，不是默认流程的一步：默认流程假定只有源码可读，运行环境不保证可得，而且此时用例目标往往还没确定，无法满足动态分析「先知道 feature」的前提。
