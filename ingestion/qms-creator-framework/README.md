# RAG-Based QMS Document Analysis & Content Creation Framework

## Overview

This framework provides a comprehensive system for analyzing your existing QMS documentation (3,598 documents), classifying them according to regulatory requirements, and generating new SOPs through an intelligent questionnaire-driven content creation process.

## Framework Components

### 1. Enhanced Content Creator Questionnaire (`content_creator_questionnaire_schema.yaml`)

A multi-level questionnaire system with:
- **10 Main Sections** covering all aspects of SOP development
- **Yes/No/Explain checkboxes** for structured data collection
- **Follow-up fields** for detailed explanations when needed
- **Custom question capability** for user-defined requirements
- **Output configuration** for tone and vocabulary level adjustment

#### Questionnaire Sections:
1. **Scope & Applicability** - Define where and how the SOP applies
2. **Regulatory Requirements** - Map to EU GMP, ICH, WHO, USP requirements
3. **Quality Attributes & Controls** - Define CQAs, CPPs, and in-process controls
4. **Equipment & Materials** - Specify equipment, materials, and PPE
5. **Documentation & Records** - Define record requirements and retention
6. **Training & Qualification** - Establish training needs and assessments
7. **Deviations & Changes** - Define deviation handling and change control
8. **Risk Management** - Document risk assessments and mitigations
9. **Process Specific** - Capture unique process requirements
10. **User Defined Questions** - Allow custom requirements capture

### 2. RAG Document Classifier (`rag_document_classifier.py`)

Automated document analysis tool that:
- **Classifies 3,598 documents** in your RAG database
- **Maps to QMS taxonomy** (QA, QC, PR, LG, HR, FE, IT, RA, RD, EHS)
- **Identifies regulatory frameworks** (EudraLex, ICH, WHO, USP, GACP)
- **Extracts themes** (19 predefined themes like cleaning validation, change control)
- **Calculates compliance scores** (0-100% based on classification completeness)
- **Generates analysis reports** in JSON or CSV format

#### Classification Dimensions:
- **Document Family**: QA, QC, Production, etc.
- **Document Type**: SOP, Form, Policy, Protocol, etc.
- **Regulatory Framework**: Which regulations apply
- **Quality Level**: Draft, Approved, Effective, Obsolete
- **Approach Type**: Procedural, Risk-based, Validation, etc.
- **Themes**: Content-based categorization

### 3. Integrated SOP Generator Workflow (`integrated_sop_generator_workflow.py`)

Complete workflow orchestration that:
- **Stage 1: Analysis** - Analyzes relevant documents from RAG database
- **Stage 2: Questionnaire** - Collects requirements through structured questions
- **Stage 3: Content Creation** - Generates SOP content using regulatory frameworks
- **Stage 4: Formatting** - Applies Purely Plant document templates
- **Stage 5: Review** - Quality checks and compliance verification

#### Key Features:
- **Regulatory Framework Analyzer** - Maps requirements to specific regulations
- **Content Generator** - Creates professional SOP content with explanatory tone
- **Template System** - Structured sections for consistency
- **Bilingual Support** - English/Macedonian output capability

## Installation & Setup

1. **Install Dependencies**
   ```bash
   pip install pyyaml
   ```

2. **Set Project Path**
   ```bash
   export QMS_PROJECT_ROOT="/home/azzu/PROJ/Cannabis EU GMP QMS Creator"
   ```

## Usage

### 1. Analyze Your RAG Database

```bash
python CONTENT_CREATOR_FRAMEWORK/rag_document_classifier.py \
    "/path/to/rag/database" \
    --output rag_classifications.json \
    --format json \
    --report classification_report.json
```

This will:
- Scan all documents in your RAG database
- Classify each according to QMS taxonomy
- Generate a compliance report
- Output classifications for further analysis

### 2. Generate New SOP

```python
from integrated_sop_generator_workflow import IntegratedSOPWorkflow

# Initialize workflow
workflow = IntegratedSOPWorkflow("/home/azzu/PROJ/Cannabis EU GMP QMS Creator")

# Define SOP request
sop_request = {
    "sop_type": "quality_control",
    "sop_name": "HPLC Testing of Cannabis Products",
    "keywords": ["HPLC", "testing", "cannabinoid", "analysis"],
    "target_audience": ["QC Analyst", "QA Personnel"],
    "department": "Quality Control"
}

# Execute workflow
results = workflow.execute_workflow(sop_request)
```

### 3. Review Questionnaire Responses

The system will present the questionnaire based on `content_creator_questionnaire_schema.yaml`. Example interaction:

```yaml
Question: "Does this SOP require specific equipment?"
Response: "Yes"
Follow-up: "List equipment with qualification status"
Response Table:
  - Equipment: "HPLC System"
    ID: "QC-EQ-001"
    Status: "IQ/OQ/PQ Complete"
    Calibration: "Yes"
```

## Integration with Existing Skills

### Content Developer Skill Enhancement
The questionnaire schema replaces simple text prompts with structured data collection:
- Multiple choice questions with validation
- Conditional follow-ups based on responses
- Table inputs for complex data
- Custom question capability

### Document Formatter Skill Integration
Generated content is passed to the formatter skill with:
- Proper document structure
- Bilingual content where required
- Department-specific formatting
- Compliance with PP templates

## Regulatory Compliance Mapping

The system automatically maps your SOPs to:

### EudraLex Volume 4
- Chapter 4: Documentation
- Chapter 5: Production
- Chapter 6: Quality Control
- Annex 15: Qualification and Validation

### ICH Guidelines
- Q7: GMP for APIs (cannabis as starting material)
- Q8: Pharmaceutical Development
- Q9: Quality Risk Management
- Q10: Pharmaceutical Quality System

### WHO GMP
- Botanical product requirements
- GACP compliance for cultivation

### USP Chapters
- <1224> Transfer of Analytical Procedures
- <1225> Validation of Compendial Procedures
- <1226> Verification of Compendial Procedures

## Output Examples

### Classification Report
```json
{
  "summary": {
    "total_documents": 3598,
    "average_compliance_score": 0.78
  },
  "by_family": {
    "QC": 1247,
    "QA": 892,
    "PR": 634
  },
  "by_regulatory_framework": {
    "EudraLex Volume 4": 2134,
    "ICH Q7": 478,
    "GACP": 156
  }
}
```

### Generated SOP Structure
```markdown
# HPLC Testing of Cannabis Products

## 1. PURPOSE
This SOP establishes the systematic approach for HPLC testing...

## 2. SCOPE
### 2.1 Applicability
This procedure applies to all QC laboratory testing...

## 3. RESPONSIBILITIES
### 3.1 QC Analyst
- Perform testing according to approved methods
- Maintain equipment calibration status
```

## Benefits

1. **Comprehensive Analysis**: Understand your entire 3,598 document knowledge base
2. **Regulatory Alignment**: Automatic mapping to EU GMP, ICH, WHO requirements
3. **Structured Approach**: Replace ad-hoc questions with systematic questionnaires
4. **Quality Consistency**: All SOPs follow the same rigorous development process
5. **Efficiency**: Leverage existing documents to inform new SOP creation
6. **Compliance Scoring**: Identify gaps in current documentation
7. **Professional Output**: Academic tone with operator-friendly explanations

## Next Steps

1. Run the RAG classifier on your complete document database
2. Review the classification report to identify gaps
3. Use the integrated workflow to generate priority SOPs
4. Customize the questionnaire schema for your specific needs
5. Integrate with your existing document management system

## Support

For questions or customization needs, refer to:
- EudraLex Volume 4 Chapter 4 (Documentation)
- ICH Q10 (Pharmaceutical Quality System)
- Your internal QA-01-001 Document Control SOP