import streamlit as st
import requests
import json
import time
from PIL import Image
import io

# Set page config
st.set_page_config(page_title="Receipt Claim Validator", layout="wide")

# Custom CSS for timeline styling with timeline on one side (left)
st.markdown("""
<style>
    .timeline {
        position: relative;
        max-width: 400px;
        margin: 0;
    }
    .timeline::after {
        content: '';
        position: absolute;
        width: 6px;
        background-color: #1E88E5;
        top: 0;
        bottom: 0;
        left: 30px;
        margin-left: -3px;
    }
    .container {
        padding: 10px 40px;
        position: relative;
        background-color: inherit;
        width: 100%;
        margin-left: 30px;
    }
    .container::after {
        content: '';
        position: absolute;
        width: 25px;
        height: 25px;
        left: -13px;
        background-color: white;
        border: 4px solid #1E88E5;
        top: 15px;
        border-radius: 50%;
        z-index: 1;
    }
    .container::before {
        content: " ";
        height: 0;
        position: absolute;
        top: 22px;
        width: 0;
        z-index: 1;
        left: 30px;
        border: medium solid #F1F5F9;
        border-width: 10px 10px 10px 0;
        border-color: transparent #F1F5F9 transparent transparent;
    }
    .content {
        padding: 20px 30px;
        background-color: #F1F5F9;
        position: relative;
        border-radius: 6px;
    }
    
    /* Timeline circle active state */
    .active-circle::after {
        background-color: #1E88E5 !important;
        border: 4px solid white !important;
    }
    
    /* Approval buttons styling */
    .stButton>button {
            
        width: 100%;
        border-radius: 4px;
        padding: 10px 24px;
        margin: 10px 0;
    }
    
    /* Form styling */
    div[data-testid="stForm"] {
        background-color: #F1F5F9;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    
    /* Card headers */
    .card-header {
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
        color: #1E88E5;
    }
    
    /* Decision placeholder */
    .decision-placeholder {
        padding: 20px;
        border: 2px dashed #ccc;
        border-radius: 6px;
        text-align: center;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)


if 'submission_result' not in st.session_state:
    st.session_state.submission_result = None
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 0  
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'decision_made' not in st.session_state:
    st.session_state.decision_made = False
if 'decision_text' not in st.session_state:
    st.session_state.decision_text = ""
if 'is_approved' not in st.session_state:
    st.session_state.is_approved = False
if 'reference_number' not in st.session_state:
    st.session_state.reference_number = ""



def render_timeline():
    phases = ["Under Review", "Under Processing", "Claim Decision"]
    
    st.markdown("<div class='timeline'>", unsafe_allow_html=True)
    
    for i, phase in enumerate(phases):
        active = i < 2 or st.session_state.decision_made
        circle_class = " active-circle" if active else ""

        st.markdown(f"""
        <div class='container{circle_class}'>
            <div class='content'>
                <h2>{phase}</h2>
                <div id='phase-{i+1}-content'>
                    <div class='{"completed" if active else "pending"}'>
                        {"Completed" if active else "Pending"}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Function to approve claim
def approve_claim():
    st.session_state.decision_made = True
    st.session_state.is_approved = True
    st.session_state.reference_number = "CL-" + str(int(time.time()))[-6:]
    st.session_state.decision_text = f"✅ Claim has been approved! Reference #{st.session_state.reference_number}"

# Function to reject claim
def reject_claim():
    st.session_state.decision_made = True
    st.session_state.is_approved = False
    # st.session_state.decis
    st.session_state.decision_text = "❌ Claim has been rejected."

# Main app layout
st.title("Receipt Claim Processing")

# Initial form (Phase 0)
if st.session_state.current_phase == 0:
    with st.form("claim_form"):
        st.subheader("Submit New Claim")
        
        # Form fields
        name = st.text_input("Full Name")
        claim_type = st.selectbox("Claim Type", ["Hotel", "Travel", "Medical", "Other"])
        claim_amount = st.number_input("Claim Amount ($)", min_value=0.0, step=10.0)
        receipt_file = st.file_uploader("Upload Receipt", type=["jpg", "jpeg", "png"])
        
        # Submit button
        submit_button = st.form_submit_button("Submit Claim")
        
        if submit_button:
            if not name or not claim_type or claim_amount <= 0 or not receipt_file:
                st.error("Please fill all fields and upload a receipt.")
            else:
                # Show loading spinner
                with st.spinner("Processing your claim..."):
                    try:
                        # Save the uploaded file temporarily
                        bytes_data = receipt_file.getvalue()
                        
                        # Create a multipart form request
                        files = {"receipt": (receipt_file.name, bytes_data, "image/png")}
                        data = {
                            "name": name,
                            "claim_type": claim_type,
                            "claim_amt": str(claim_amount)
                        }
                        
                        # Send the request to the backend
                        response = requests.post("https://receipt-service-genai.azurewebsites.net/Form-data", files=files, data=data)
                        
                        if response.status_code == 200:
                            # Store the result in session state
                        
                            st.session_state.submission_result = response.json()
                            st.session_state.current_phase = 1  # Move to Results phase
                            st.session_state.form_submitted = True
                            st.rerun()
                        else:

                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

# After form submission, show the timeline and all results at once
if st.session_state.form_submitted and st.session_state.submission_result:
    # Display results and timeline in two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Claim Processing Results")
        results = st.session_state.submission_result
        
        # Step 1: Claim Submitted - Display each field separately
        st.markdown("<div class='card-header'>📋 STEP 1: Claim Submitted</div>", unsafe_allow_html=True)
        
        # Parse the claim information from the results string
        print(results)
        claim_info = results["Claim_Submitted"]
        
        # Create a container for better styling
        with st.container():
            # Extract and display each field separately with blue background
            if "**Name**:" in claim_info:
                name_parts = claim_info.split("**Name**:")[1].split("**Claims Type**:")[0].strip()
                st.info(f"**Name**: {name_parts}")
            
            if "**Claims Type**:" in claim_info:
                type_parts = claim_info.split("**Claims Type**:")[1].split("**Amount**:")[0].strip()
                st.info(f"**Claims Type**: {type_parts}")
            
            if "**Amount**:" in claim_info:
                amount_parts = claim_info.split("**Amount**:")[1].strip()
                st.info(f"**Amount**: ${amount_parts}")
        
        
        # Step 2: Under Processing
        st.markdown("<div class='card-header'>🔍 STEP 2: Under Review</div>", unsafe_allow_html=True)
        st.info(results["Under_Review"])
        
        
        # Step 3: Claim Decision
        st.markdown("<div class='card-header'>📝 STEP 3:Under Processing</div>", unsafe_allow_html=True)
        st.info(results["Under_Processing"])        
       
        if st.session_state.decision_made:
            if st.session_state.is_approved:
                st.success(st.session_state.decision_text)
            else:
                st.error(st.session_state.decision_text)
        else:
            st.markdown("<div class='decision-placeholder'>Decision pending. Please approve or reject the claim below.</div>", unsafe_allow_html=True)
            
            # Display approval buttons
            st.subheader("Claim Decision")
            approval_col1, approval_col2 = st.columns(2)
            
            with approval_col1:
                if st.button("✅ Approve Claim", key="approve", type="primary"):
                    approve_claim()
                    st.rerun()
            
            with approval_col2:
                if st.button("❌ Reject Claim", key="reject"):
                    reject_claim()
                    st.rerun()
    
    # Column 2: Display timeline on the right
    with col2:
        st.subheader("Claim Timeline")
        render_timeline()

# Reset button
if st.session_state.form_submitted:
    if st.button("Submit New Claim"):
        # Reset session state
        
        st.session_state.submission_result = None
        st.session_state.current_phase = 0
        st.session_state.form_submitted = False
        st.session_state.decision_made = False
        st.session_state.decision_text = ""
        st.session_state.is_approved = False
        st.session_state.reference_number = ""
        st.rerun()
