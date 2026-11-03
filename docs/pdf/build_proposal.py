"""Current proposal. Shared pages; source notes appear only in the wide private copy."""
from pathlib import Path
from copy import deepcopy
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.platypus import Image,Spacer,Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from pypdf import PdfReader,PdfWriter,PageObject
import layout as base
from runpy import run_path
from layout import section,p,sub,table,callout,ServiceCircle
ROOT=base.ROOT
OUT=ROOT/'output/pdf'
pages=[]; notes=[]
def add(title,body,refs,k='PROJECT FARO | DESIGN PROPOSAL'):
    pages.append(section(k,title,*body)); notes.append(refs)
def rows(a,b,data):return table([a,b],data,[170,313])
def R(label,path,detail):return (label,Path(path),detail)
def demo(label,path,detail):return R(label,ROOT/'demo'/path,detail)
def svc(name):
    detail={"compass":"Coordinates each turn and the service calls.","signal":"Uses the classification result to continue, clarify or stop.","bridge":"Reads permitted sources and returns findings with evidence IDs.","shield":"Replays the reads and releases only supported findings.","voice":"Explains checked findings or states why a result is withheld."}[name]
    suf='faro_signal' if name=='signal' else name
    module={'compass':'orchestrator','signal':'classifier','bridge':'reader','shield':'verifier','voice':'generator'}[name]
    file=next((ROOT/'demo'/name).glob(f'*/infer/{name}/{name}/{module}.py'))
    return R(name.title()+' | current demo',file,detail)
H=Path.home()
luna=R('Luna | question rewriting',H/'machine-learning-luna/luna/predictor/predictor.py','Original pattern: combine the user’s messages into one standalone question.')
nemo=R('Nemo | knowledge search',H/'machine-learning-nemo/nemo/predictor.py','Existing search method. Faro changes the search backend, not the role of retrieval.')
japan=R('Japan | follow-up',H/'machine-learning-japan/japan/predictor.py','Original pattern for asking only when the information supplied is insufficient.')
analytics=R('AI2Analytics | forwarding',H/'machine-learning-ai2analytics/service/ai2analytics/proxy_handler.py','Source pattern for service forwarding. Not a production sign-in system.')
forecast=R('Forecasting | input normalization',H/'Projects/automated-forecasting-engine-commodities/src/market_forecasting_engine/data.py','Related pattern for standardizing incoming names and dates; not a ready-made terminal connector.')
records=demo('Faro | record checks','bridge/machine-learning-bridge-api/infer/bridge/bridge/records.py','Checks revisions, deletion markers, dates, coverage and approved measures.')
source=demo('Faro | permitted sources','bridge/machine-learning-bridge-api/infer/bridge/bridge/source.py','Builds the catalogue and reads only the permitted operational records.')
retry=demo('Faro | attempt recording','utils/utils/llms/model_attempts.py','Records each model attempt under the service and turn that made it.')
schema=demo('Faro | field origins','compass/machine-learning-compass-api/infer/compass/compass/collection_schema.py','Defines each stored column and where its value comes from.')
store=demo('Faro | owned collection','compass/machine-learning-compass-api/infer/compass/compass/data_collection.py','Conversation ownership, saved turns, versioned caches and exported attempts.')
live=R('Faro | saved retry example',ROOT/'docs/validation/retry_example.json','Historical verified demo report; not a client-performance benchmark.')
sql=R('Faro | proposed SQL tables',ROOT/'docs/data_collection_schema.sql','Product storage design, separate from client source systems.')
readers=demo('Connector | three file readers','connector/machine-learning-connector-api/infer/connector/connector/readers.py','A registry selects a reader by file type; the readers preserve native names, values and references.')
tests=demo('Connector | evidence tests','connector/machine-learning-connector-api/tests/test_sources.py','Access, three formats, an unrelated table, changed records and incomplete links.')
joined=demo('Bridge | linked records','bridge/machine-learning-bridge-api/infer/bridge/bridge/connected.py','Reads original records and verifies that selected keys can connect the two tables.')
fixture=demo('Harbor | three source files','scripts/create_connector_sources.py','Recreates the example release. The operations note explains how the records fit together.')
factory=R('Trading projects | reader selection pattern',H/'Projects/invest-alpaca-bear-put-eth-test/ai_trading_system/trader/profile_factory.py','Related pattern for choosing an implementation. The native readers are new.')
add('Project Faro',[
 p('Ask your terminal data. Understand the answer.','Sub'),
 Image(str(ROOT/'output/imagegen/project_faro.png'),width=483,height=150,kind='proportional'),Spacer(1,8),base.heading('TL;DR'),
 p('The client connects the data their staff may use. Maria selects her account and asks a question in plain English. She does not need to write a glossary, rename columns or tell Faro how to join files.'),
 p('Faro uses connectors: a connector is the part that knows how to read a particular source, such as a database, a report or a spreadsheet. Faro can connect to a client’s existing data lake, but the client does not need to build one. It explains what it found, where it came from and what the records cannot establish.'),
 p('In the demo, one client provides three files. The database records idle minutes, a spreadsheet names the berth for each posting, and a PDF explains which postings count. Faro uses all three to answer Maria. If a posting has no berth, it explains why it cannot name a winner.'),
 callout('Why Faro?','Faro means lighthouse. Its job is to show the operator what the records support and where the evidence stops.')],[fixture,readers])
add('1. The client connects data. Maria asks.',[
 p('Maria asks: <b>“Which berths had the most crane idle hours last month?”</b> She knows the operational question. She should not need to know whether the answer lives on page six of a report or across two tables.'),
 sub('What Faro prepares behind the scenes'),
 p('Faro lists only the files Maria may see. It can inspect their headings, read their records and point back to the original page, sheet or database result. These three examples show why finding a file and understanding its contents are different steps.'),
 rows('What Faro sees','How it uses the information',[
 ['An October operations report','Index its headings and table locations. A table labelled “idle hours by berth” is a promising place to look; its month, units, coverage and version still need checking.'],
 ['Two equipment names','A spreadsheet says C07; a database says QC-7. Look for a shared equipment ID or an existing register that links them. Similar spelling alone is not enough to combine their hours.'],
 ['Only a current berth assignment','That can locate the crane today. It cannot put last month’s hours on a berth. Keep the terminal records usable and leave the historical berth unknown.']]),
 callout('When to ask Maria','Ask only when her preference could change the answer. “Most idle hours” is already clear. If she says “worst” and total hours and idle percentage give different winners, show the distinction or ask which she wants. Do not ask her to map the database.')],[source,forecast])
add('1.1 One product, interchangeable connectors',[
 p('Each connector answers the same three requests. The client keeps its infrastructure; the connector translates Faro’s request into a read that its source supports. The rest of Faro does not need to know whether that means querying a database or opening a workbook.'),
 rows('What Faro asks','What the connector returns',[
 ['List what Maria may see','Names and references for permitted sources only. Access is checked for this client and user before discovery or reading.'],
 ['Describe what is there','Native field names, location and file version. Units and meanings come from the source material when present; a column heading alone does not prove them.'],
 ['Read the needed part','Requested values with a precise reference: record IDs, PDF page, or workbook sheet and row. Include the source version or snapshot when available; say when freshness or coverage cannot be checked.']]),
 sub('What changes when the next client connects'),
 p('For a supported source, configure its location, credentials and access scope. The connector handles its file layout or query method. A previously unseen format may need a reader built once and reused for other clients. Names and evidence can differ even when the format is the same.'),
 callout('What stays in Faro','Gate checks access; Scout finds candidate sources; Bridge decides what to read; Shield checks whether those facts support the answer. None needs a special rule for Client A’s berths. Faro’s own collection of turns, checks and cache entries stays separate from the client’s source material.')],[readers,factory,analytics])
add('1.2 What runs today and what comes next',[
 p('The local demo reads SQLite, Excel and text PDFs through a separate Connector service. Its readers open the files. They do not decide which entries count as idle time or which terminal performed better.'),
 table(['Service','Working in the demo','Still to build'],[
 ['Scout | find where to look','Searches company definitions and lists the permitted tables, sheets and PDF.','Index newly connected file contents for search at large scale.'],
 ['Bridge | get the facts','Reads source notes and records. Can link two tables by matching fields and compare the resulting values.','Support larger sources, scanned reports and relationships that depend on overlapping time intervals.'],
 ['Shield | check the answer','Repeats the reads and checks the proposed findings against their source versions and rows.','Test against real client revisions, access policies and independently reviewed answers.']],[105,180,198]),
 callout('Current boundary','The local demo selects a saved user account; production sign-in is still needed. Connected files are granted as a whole. Reads stop above 500 rows. The expression worker is isolated on macOS; other operating systems need an equivalent worker.'),
 sub('What stays reusable across clients'),
 p('Clients keep their own formats and meanings. Faro standardizes what accompanies an answer: the measure, scope, dates, source, version and known gaps. A new format may need a reader; it does not need a new conversation or checking service.'),
 p('For changing records, follow the source’s revisions: count a correction once, exclude a record whose latest version marks it deleted, and recheck coverage when late entries arrive. If two versions cannot reliably be matched, do not present an exact total from them.')],[nemo,readers,joined,svc('shield')])
add('2. From a question to an answer',[
 p('Maria is an example terminal operator. She sees one screen. Compass coordinates the services below; it keeps her question, replies and evidence together.'),
 ServiceCircle(),
 rows('What comes in','What moves forward',[
 ['Question and signed-in account','Gate checks the person and permitted sites. Library supplies company terms and available sources within that access.'],
 ['Question and approved terms','Thread uses relevant replies; Scout searches definitions. Signal decides whether to continue. Guide asks one question if a choice that matters is missing.'],
 ['Clear request and permitted sources','Connector opens the files for Scout, Bridge and Shield. Bridge reads the data. Shield independently checks the evidence. Voice explains only supported findings. Compass saves the turn.']])],[analytics,svc('compass')])
add('2.1 Maria asks about crane idle time',[
 p('Maria asks: <b>“Which berths had the most crane idle hours last month?”</b> The measure is clear. The open question is whether her records actually identify the berth. Being allowed to see two terminals does not establish either answer.'),
 rows('Step','Input → work → output',[
 ['Gate | check access','Maria selects her demo account. Her account permits North and South at Harbor. Her words cannot grant access to another company. Library loads the prepared Harbor catalogue.'],
 ['Thread | understand replies','On the first turn, keep her question as asked. On later turns, combine her answer with the original request. Never borrow a choice from someone else’s conversation.'],
 ['Scout | find the meaning','Search Harbor’s approved documents for idle time. Return the text and source: idle time is when a crane is available but not working. This is a definition, not a ranking.'],
 ['Signal and Guide | clarify','Signal uses the Decision API only to classify the next step. If both total idle hours and idle share are legitimate interpretations, Guide asks which she means. If her wording or the source already settles it, proceed.']]),
 callout('When a follow-up is useful','Maria already said “most crane idle hours,” so skip the follow-up. If she had said only “worst,” Guide could ask “Most total idle hours, or largest idle share?” Thread would keep her reply with the original question.'),
 p('For a question asked on 1 November 2026 in the client’s local time, “last month” means 1–31 October. The date range travels with the request.')],[luna,nemo,japan,svc('signal')])
add('2.2 Read what Maria is allowed to see',[
 p('Bridge receives the clarified question and the full catalogue of sources Maria may use. Scout’s search results help explain terms; they do not restrict Bridge to one document or require every question to be a ranking.'),
 sub('One client, three sources'),
 rows('Source','What it adds to the answer',[
 ['SQLite database','The current entries give the activity code and minutes for each work reference. The source provides a view that accounts for corrections and withdrawals.'],
 ['Excel workbook','Each work reference is assigned to a berth. This lets Faro place the recorded idle time at the right berth.'],
 ['PDF operations note','Page 1 identifies October, explains which code counts as idle, and says which references connect the two files. It contains no ranking.']]),
 callout('Why all three matter','A database row gives minutes but no berth. The workbook gives a berth but no minutes. The note tells Faro when it is valid to combine them. Maria supplies none of these instructions herself.')],[fixture,readers,joined])
add('2.3 Follow one question across three files',[
 sub('1. Find the records'),
 p('Scout returns the idle-time definition and the list of permitted sources. Bridge reads the October note. It learns that database field “ticket” and workbook field “Work reference” identify the same posting.'),
 sub('2. Connect the records'),
 p('Bridge reads the current entries and the assignment sheet. It checks that the references match and that each posting has one berth. It groups the counted minutes by berth, then converts minutes to hours. Each read keeps the original location and file version.'),
 sub('3. Check the result'),
 p('Shield opens the sources again and checks the evidence. With the complete October release, the ranking is S1: 115 hours, N1: 100, N2: 86 and S2: 71.'),
 callout('Change just one thing','Remove one assignment from the workbook and ask the same question. The database still has the idle minutes, but Faro cannot tell which berth should receive them. The console withholds the ranking. Maria is told why instead of being shown a different winner.')],[fixture,joined,tests,svc('shield')])
add('2.4 Check the result before speaking',[
 p('Shield receives the proposed findings and the records Bridge used. It repeats each read independently on the permitted source. It checks the source version, period, completeness, grouping and numbers; then it checks whether the words say more than the evidence.'),
 rows('What might go wrong','What the check does',[
 ['The two terminals tie','Keep both at 186 idle hours. A request for one “worst” terminal is not evidence that one exists.'],
 ['A record arrived late or was withdrawn','Re-read the current revisions. If a missing day could change the order, withhold the ranking. State which site or date is affected rather than calling the whole catalogue empty.'],
 ['Rounding changes a decision','In October, South C01 made 4,678 moves in 234 operating hours: 19.99145 moves/hour. A screen rounded to 20.0 hides that it fell below a target of 20. Compare before rounding.']]),
 sub('Voice | explain only what passed'),
 p('“For 1–31 October, berth S1 recorded the most crane idle time: 115 hours. N1 followed at 100, N2 at 86 and S2 at 71.” The answer should make the indicator, dates, scope, source and limits visible. Compass retains the checked evidence for inspection.'),
 callout('Open the evidence','Below the answer, Faro returns the document name and a link. Connected files are saved as they were read, with the version retained. For shared JSON data, it returns only the permitted records, not another company’s records. Links open local files in the demo.'),
 callout('If part of a claim fails' ,'Release an independently supported narrower finding if possible. If no finding can be verified, withhold the result and say why. A confident model answer is not a substitute for this check.')],[svc('shield'),svc('voice'),records])
add('2.5 A different question: why did dwell time spike?',[
 p('Maria asks: <b>“Why did dwell time spike for reefer containers in week 12?”</b> A reefer is a refrigerated container. This question asks Faro to establish both a change and its cause. Those require different evidence.'),
 rows('Question to settle','What would support an answer',[
 ['What is being compared?','Use the agreed start and end events for dwell time, the client’s local week, the site and a comparison period. If the year or baseline matters and cannot be inferred, ask once.'],
 ['Was there a spike?','Identify reefer containers, check the relevant event times and coverage in both periods, and compare using the agreed measure. A longer stay for one container does not prove a general spike.'],
 ['Why did it happen?','To attribute a cause, require supporting event records tied to the affected containers and dates. A delay that happened at the same time is not proof that it caused the increase.']]),
 callout('What Faro can say with the current Harbor catalogue','“These records cover crane activity, not reefer arrival and departure events. I can’t establish whether dwell time rose in week 12 or why.” Do not substitute crane downtime for container dwell time.'),
 p('With a client that supplies dwell events but no reliable cause records, Faro can report the measured change and explicitly leave the cause unanswered. Faro explains that limit without asking Maria to reconcile files.')],[source,svc('shield')])
add('3. Keep repeated questions affordable',[
 p('Prepare the source guide once and refresh only what changes. Prefer a current reviewed report when it already answers the question; reading one table can avoid repeated work across raw files. Keep the same permission and evidence checks whichever route is used.'),
 rows('Where the saving comes from','What remains protected',[
 ['Prepare once; search many times','Build the company’s search index upfront. At question time, turn only the question into a search representation. Refresh the index when the approved documents change.'],
 ['Reuse checked data','While Maria is away, Luis asks the same question. Compass may use a saved read if the company, permitted scope, question, period and versions still match. Shield checks it again. A correction or changed access invalidates reuse.'],
 ['Reuse model work','Keep successful model results in a separate company cache. Match the actual inputs, settings and permissions, including user scope. A clarification changes the inputs. A cache hit avoids the call; a failed result is not saved as a success.'],
 ['Use only the model work needed','Signal uses a classification call. The shared model settings give different work different reasoning effort. Counts, sums and permission checks do not require a model to guess a number.']]),
 callout('How to judge the trade-off','Track elapsed time, calls, retries, cache hits and cost per verified answer, by company. Review slow requests too, not just averages. Compare faster or cheaper settings against the same reviewed questions before adopting them.')],[nemo,store,demo('Shared utils | model levels','utils/utils/llms/common/intelligence_level.py','YOLO and LIGHT currently select the same model with different effort. Signal’s Decision API selects its model explicitly.')])
add('3.1 When a service times out',[
 p('A slow model call does not justify restarting Maria’s question. Retry only the failed call, up to three attempts total, for a temporary provider failure. Do not repeat an access denial or a failed evidence check. If Shield cannot verify after retries, it returns no figures.'),
 sub('One saved demo turn'),
 p('Maria requested a performance report for cranes by terminal. Signal classified the request once. Bridge made two successful model calls: two separate pieces of work, not two retries. Shield timed out on its first call, succeeded on the retry, then made a second successful call.'),
 rows('Service | job','Attempts in that turn',[
 ['Signal | classify','1: success.'],['Bridge | read the facts','2: success; success.'],['Shield | verify findings','3: timeout → success on the same call; success on a separate call.']]),
 callout('What the record tells us','The report was verified in about 95 seconds. The retry worked, but the operator still waited. This single demo run shows where time was spent; it does not establish typical speed, client savings or an acceptable wait.'),
 p('Compass saves the question and turns. Each model service records its own attempts so a timeout remains visible even if its response never reaches Compass. Existing successful work stays attached to the original turn.')],[live,retry,R('Japan | retry pattern',H/'machine-learning-japan/japan/common_tools/llm_handler.py','Backoff around the model call, not around the conversation.')])
add('4. Find out whether operators would use Faro',[
 p('Choose recurring tasks with the terminal supervisor: preparing the morning report, comparing idle time or checking a target. Start with tasks people already complete by searching files and emailing colleagues. Success is reaching a sound operational decision with less effort.'),
 rows('Pilot step','Evidence to collect',[
 ['Before the pilot','Ask operators to complete representative tasks the current way. Record elapsed time, handoffs and whether they found a usable answer. Have a data owner independently establish the expected numbers, scope and acceptable reasons to withhold.'],
 ['Run both methods','Use comparable tasks and source versions. Include incomplete periods, ties, corrections, ambiguous names, changed permissions and unsupported causes. Review errors and unnecessary refusals, not only successful answers.'],
 ['Watch the decision','Can the operator explain what the figures mean and what they do not prove? Would they act, ask for more data, or investigate? Record when an answer changes a decision and whether the reviewer agrees.'],
 ['Decide whether to expand','Compare task completion, time saved, corrections, cost per completed task and repeat use without prompting. Agree thresholds with the client before the pilot. Stop rollout for unauthorized disclosure or materially misleading claims.']]),
 callout('One concrete acceptance case','Use the same question twice. With complete assignments the correct winner is S1. With an assignment missing, the correct outcome is to explain the gap without naming a winner. Always test both halves: refusing everything is not useful either.'),
 p('A repeatable demo proves the services can work together. Only a client pilot can show whether operators trust the answer enough to use it and whether it improves their work.')],[live,demo('Faro | live conversation regression','tests/test_maria_analysis_console.py','Exercises the console journey; not evidence of adoption.'),R('Semantica | evaluation pattern',H/'Projects/Semantica/openend_quality/evaluation/compare_five.py','Related example of repeatable comparisons; client utility still needs observation.')])
add('4.1 Check the same design in other sectors',[
 p('A reusable design must work when the client’s vocabulary changes. The same services answered questions about terminal idle time, retail sales, hospital occupancy and hotel counts in the current console test. This is evidence of those examples, not proof of every possible source or sector.'),
 rows('Example','What the test established',[
 ['Terminal operations','One question used a database, a workbook and a PDF, returning the supported berth ranking and the files used.'],
 ['Retail','The model answered a total-sales question without a ranking requirement.'],
 ['Hospitals','Six hospitals have July–October records covering occupancy, visits, waiting time, admissions, discharges and cancellations. A separate check confirms that a missing reporting day is not zero.'],
 ['Hotels','An inventory count worked without requiring a date range.']]),
 callout('Stress the boundaries','Automated checks also use unfamiliar column names and a new recycling example. They test company isolation, duplicate or missing links, changed records, oversized reads and attempts to access files or the network. These are bounded checks, not a production security audit.')
],[R('Faro | live sector results',ROOT/'docs/validation/sector_results.json','Observed console answers and their model explanations.'),demo('Faro | generic stress tests','tests/test_sector_stress.py','Unseen names, company isolation, read limits and execution boundaries.')])
add('4.2 Keep each decision understandable',[
 p('The service names describe their work: Compass coordinates, Thread rewrites, Signal classifies, Guide generates a follow-up, Bridge reads, Shield verifies and Voice presents the answer. The shared model utilities keep their original prediction interface.'),
 sub('What the model returns'),
 p('Each model prompt follows the same structure: objective, supplied information, initial analysis, final reasoning and response. The initial analysis briefly identifies relevant facts or gaps. The reasoning briefly explains the selected result. These summaries support review; they are not proof that an answer is correct.'),
 sub('What is saved'),
 p('Each model-call record stores the service, turn, call ID, attempt outcomes and the assessment and reasoning returned for that attempt. Separate Bridge reads remain separate calls. A reused answer points back to its producing turn; the cache does not invent a new explanation.'),
 callout('Classification stays classification','Signal asks for the action, assessment and justification as three choices in the same Decision API call. It does not replace classification with a full free-text generation call. Other model responses use the Pydantic schema beside their prompt.')
],[japan,R('Gambit | analysis and response pattern',H/'machine-learning-gambit/gambit/predictor_files/prompts/maker/ai_attributes/ai_attributes_prompt.py','Role, objective, analysis, reasoning and response sections adapted to Faro.'),retry])
columns = run_path(str(ROOT/"demo/compass/machine-learning-compass-api/infer/compass/compass/collection_schema.py"))["COLUMNS"]
def schema_rows(name):
    return table(["SQL column","Type","Where the value comes from"],
        [[col,kind,origin] for col,kind,origin in columns[name]], [123,82,278])
add("A.1 One row per conversation",[
    p("Faro owns these SQL tables. Client files stay separate. One conversation has many turns; each saved result points back to the turn that produced it."),
    schema_rows("conversations"),
    callout("Maria’s example","Compass assigns the conversation ID. Gate supplies her company and account. Her clarification reply stays in that same conversation.")
],[store,sql],k="DATA COLLECTION | SQL DESIGN AND FIELD ORIGINS")
add("A.2 One row per turn",[
    p("The turns table preserves what happened to each user message, including a clarification or failure."),
    schema_rows("turns")
],[schema,sql],k="DATA COLLECTION | SQL DESIGN AND FIELD ORIGINS")
add("A.3 Two caches, one lookup pattern",[
    p("ai_cache holds successful model results. data_cache holds evidence that passed Shield. A cache entry points back to its originating turn."),
    schema_rows("ai_cache"),
    callout("Keep the checks","Gate checks access again; Shield rechecks reused evidence. A change of company, permissions, wording, definitions, source version or model settings invalidates the relevant saved work.")
],[store,sql],k="DATA COLLECTION | SQL DESIGN AND FIELD ORIGINS")
add('A.4 Trace an answer and its model calls',[
 p('Faro’s SQL design stores one model_calls row per logical model call. The turn ID links it back to the original question. Two reads are separate calls; a retry is another attempt inside the same call.'),
 schema_rows('model_calls'),sub('Field origins'),schema_rows('field_origins'),
 p('Thread supplies the rewritten question. Scout supplies matching definitions and sources. Signal classifies the next action; Guide asks the follow-up if needed. Bridge supplies reads and evidence. Shield supplies verified findings or a reason for withholding. Voice supplies the answer. Compass records the turn outcome and cache use.'),
 callout('How to read the attempt history','A timeout followed by success inside one call means the retry worked. No entry means the service made no model call on a tracked turn. Older turns without tracking are unknown, not zero.')],[schema,retry,sql],k='DATA COLLECTION | SQL DESIGN AND FIELD ORIGINS')
base.build('terminal_data_proposal.pdf',pages)
public=OUT/'terminal_data_proposal.pdf'
reader=PdfReader(public);assert len(reader.pages)==len(pages),(len(reader.pages),len(pages))
writer=PdfWriter()
for i,(page,refs) in enumerate(zip(reader.pages,notes),1):
 stream=BytesIO();c=canvas.Canvas(stream,pagesize=(872,841.89))
 c.setFillColorRGB(.95,.97,.98);c.rect(601,49,260,746,fill=1,stroke=0)
 c.setFillColorRGB(1,1,1);c.rect(45,17,225,21,fill=1,stroke=0)
 c.setFillColorRGB(.3,.36,.43);c.setFont('DocArial',8);c.drawString(56,29,'PERSONAL REFERENCE COPY')
 x,y=615,775
 def draw(txt,sz=10,bold=False,gap=8):
    global y
    q=Paragraph(txt,ParagraphStyle('note',fontName='DocArialBold' if bold else 'DocArial',fontSize=sz,leading=sz+4,textColor='#243850'));_,h=q.wrap(228,750)
    y-=h;q.drawOn(c,x,y);y-=gap
 draw('PROJECT REFERENCES',12,True)
 for label,path,detail in refs:
    if path.is_relative_to(ROOT):
        target = "https://github.com/RuddiRodriguez/project-faro/blob/main/" + path.relative_to(ROOT).as_posix()
    else:
        target = path.as_uri()
    draw(escape(label),10,True,2);draw('<link color="#007F82" href="'+escape(target)+'"><u>Open source</u></link>',9,False,4);draw(escape(detail),10,False,14)
 assert y>54
 c.showPage();c.save()
 out=PageObject.create_blank_page(width=872,height=841.89);out.merge_page(page);out.merge_page(PdfReader(stream).pages[0]);writer.add_page(out)
writer.add_metadata({'/Title':'Project Faro | Proposal with project references'})
writer.write(OUT/'terminal_data_proposal_with_project_references.pdf')
print(len(pages),'pages per edition')
