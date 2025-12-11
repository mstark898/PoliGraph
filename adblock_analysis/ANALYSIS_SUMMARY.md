
=== PoliGraph Analysis Summary for AdBlock Privacy Policy ===

SETUP COMPLETED:
✅ PoliGraph environment configured with Python 3.10 and spaCy transformer model
✅ Modified NER pipeline to work with built-in entity recognition
✅ Fixed entity type mapping (NN entities treated as DATA, ACTOR entities preserved)
✅ Ran complete PoliGraph pipeline: crawler → init_document → annotators → build_graph

KNOWLEDGE GRAPH RESULTS:
📊 Generated files in adblock_analysis/:
   - graph-original.yml (3,325 bytes) - Human-readable YAML format
   - graph-original.graphml (6,362 bytes) - Machine-readable GraphML for visualization
   - document.pickle (164,939 bytes) - Processed NLP data with 129 segments

ENTITIES DISCOVERED:
👥 ACTORS: 'we' (AdBlock company)
📋 DATA TYPES:
   - 'ip address' - IP addresses collected from website visits
   - 'personal information' - GDPR-compliant personal data collection
   - 'cookie / pixel tag' - Website cookies for user experience
   - 'personal identifier' - User ID statistics and identifiers
   - 'aggregate / deidentified / pseudonymized information' - Anonymized data sharing
   - 'UNSPECIFIED_DATA' - General data collection references

RELATIONSHIPS EXTRACTED:
🔗 All relationships show 'we' COLLECT [data_type]
📍 Each relationship includes original text excerpts from the privacy policy
🎯 Successfully identified key privacy practices in AdBlock's data handling

NEXT STEPS FOR VISUALIZATION:
1. Open graph-original.graphml in yEd, Gephi, or Cytoscape for interactive visualization
2. Use graph-original.yml for programmatic analysis or custom visualization
3. Examine specific data collection practices by reading the 'text' field for each edge

