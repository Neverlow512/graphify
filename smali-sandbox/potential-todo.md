The Graph Enhancement Reminders
Filter Resource Classes: Drop R$ classes during extraction to clean up community clustering and save massive amounts of tokens.

Extract String Literals: Create nodes for const-string opcodes to give the AI semantic anchors for renaming obfuscated logic.

Resolve Virtual Dispatch (Post-Processing): Run a Class Hierarchy Analysis (CHA) script to connect invoke-interface calls to their actual implementations.

Extract Type Casts: Track check-cast and instance-of opcodes to reveal the true identity of generic java.lang.Object parameters.

Capture Security Annotations: Extract .annotation directives to instantly expose security boundaries (like WebViews) and API networking layers.

Promote Reflection Edges: Change the edge type to calls_reflection for Method.invoke or DexClassLoader so the AI zeroes in on dynamic/hidden behavior.

Shard by Community: Always split the graph by Leiden community IDs before passing it to the LLM to prevent context-window hallucinations.

--- 

Recategorized by gemini:

Group 1: The Core 3 (Do these first)
These are the foundational fixes required to make your current graph usable for the LLM.

[EXTRACTION] Filter Resource Classes: Drop the R$ classes so your graph stops clumping together into a giant hairball.

[EXTRACTION] Extract String Literals: Add const-string so the LLM can read API keys and log messages.

[POST-PROCESSING] Resolve Virtual Dispatch (CHA): Write the script that runs after extraction to connect interfaces to their implementations.

Group 2: The Extra 3 (Do these later)
Once the Core 3 are working, you add these into your extract.py file to give the LLM "cheat codes" for heavily obfuscated apps.

[EXTRACTION] Extract Type Casts: Track check-cast to see what types of objects are being passed around.

[EXTRACTION] Capture Security Annotations: Track .annotation to easily spot WebViews and network endpoints.

[EXTRACTION] Promote Reflection Edges: Flag Method.invoke as a special edge type so the AI knows where the malware is hiding.


---

And recategorized by gemini again:

1. Pure Extraction (Inside extract_smali.py)
These are literal, explicit facts found within a single .smali file. By adding these, you are simply making your parser a more complete representation of the bytecode.

Filter Resource Classes (R$): Instruct the parser to intentionally ignore auto-generated Android resource classes. They do not contain app logic.

Extract String Literals (const-string): Strings are literal data points in the bytecode. Extract them and attach them to the method where they are declared.

Extract Type Casts (check-cast / instance-of): These are explicit Dalvik opcodes. Track them to record the data types the method operates on.

Capture Annotations (.annotation): These are explicit compiler directives in the Smali file. Extract them to record the boundaries (like @JavascriptInterface).

2. Post-Processing (Operating on graph.json)
These steps happen after extraction, because they require looking at the entire application architecture at once to connect the dots.

Virtual Dispatch Resolution (CHA): Your parser sees File A calling an interface, and File B implementing it. The post-processor script reads the graph.json, finds those two separate facts, and draws a new edge connecting them.

Community Detection (Leiden Algorithm): Graphify runs this over the final graph.json to group the nodes into logical subsystems based on their structural density.