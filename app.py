import streamlit as st
from streamlit.components.v1 import html
from datetime import datetime, time
import os
from dotenv import load_dotenv
import pandas as pd

# Configure Streamlit page
st.set_page_config(
    page_title='Agranergy Energy Savings Calculator',
    page_icon='https://www.agranergy.com/assets/logo-969d5430.ico',
    layout='wide',
    menu_items={
        'Get help': None,
        'Report a bug': None,
        'About': None
    },
    initial_sidebar_state='collapsed'
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

# Load environment variables
load_dotenv()

class SmartLightingCalculator:
    def calculate_high_brightness(self, input_wattage):
        """Calculate high brightness mode wattage based on input wattage"""
        if input_wattage <= 20:
            return 10
        if input_wattage <= 24:
            return 12
        if input_wattage <= 36:
            return 16
        if input_wattage <= 60:
            return 18
        return 20  # Maximum cap at 20W

    def __init__(self):
        self.data = {
            'project_name': None,
            'total_lights': None,
            'original_wattage': None,
            'electricity_rate': None,
            'operation_schedule': {},
            'smart_light_high_wattage': None,
            'smart_light_low_wattage': None,
            'high_power_ratio': None
        }
        self.common_sense_rules = {
            'total_lights': (1, 10000),  # Reasonable range for number of lights
            'original_wattage': (1, 400),  # Common wattage range (watts)
            'electricity_rate': (0.1, 1.0),  # Reasonable electricity rate range (SGD/kWh)
            'smart_light_high_wattage': (5, 20),  # High power range for smart lights (W)
            'smart_light_low_wattage': (1, 5)   # Low power range for smart lights (W)
        }

    def validate_input(self, key, value):
        """Validate if the input value is within reasonable range"""
        if key in self.common_sense_rules:
            min_val, max_val = self.common_sense_rules[key]
            if not (min_val <= float(value) <= max_val):
                return False, f'Input value should be between {min_val} and {max_val}'
        return True, ''

    def calculate_savings(self):
        """Calculate energy savings"""
        if None in self.data.values():
            return None

        # Calculate detailed consumption for each period
        period_details = []
        original_daily_consumption = 0
        smart_daily_consumption = 0

        # Get power mode ratio
        high_power_ratio = self.data.get('high_power_ratio', 0.25)  # Default 25% if not set
        low_power_ratio = 1 - high_power_ratio

        for period in self.data['operation_schedule']:
            hours = period['duration']
            lights_on = period['lights']
            
            # Original system calculations
            period_original = (lights_on * self.data['original_wattage'] * hours) / 1000
            original_daily_consumption += period_original

            # Smart system calculations
            if lights_on > 0:  # Only calculate if lights are on
                high_hours = hours * high_power_ratio
                low_hours = hours * low_power_ratio
                period_high = (lights_on * self.data['smart_light_high_wattage'] * high_hours) / 1000
                period_low = (lights_on * self.data['smart_light_low_wattage'] * low_hours) / 1000
                period_smart = period_high + period_low
            else:  # No consumption if no lights are on
                high_hours = 0
                low_hours = 0
                period_high = 0
                period_low = 0
                period_smart = 0
            smart_daily_consumption += period_smart

            # Store period details with rounded values
            period_details.append({
                'period': f"{round(period['duration'], 2)} hours",
                'lights_on': lights_on,
                'original_consumption': round(period_original, 2),
                'smart_high_hours': round(high_hours if lights_on > 0 else 0, 2),  # Only count hours if lights are on
                'smart_low_hours': round(low_hours if lights_on > 0 else 0, 2),   # Only count hours if lights are on
                'smart_high_consumption': round(period_high, 2),
                'smart_low_consumption': round(period_low, 2),
                'smart_total_consumption': round(period_smart, 2),
                'period_savings': round(period_original - period_smart, 2)
            })

        # Calculate total savings
        daily_savings_kwh = original_daily_consumption - smart_daily_consumption
        annual_savings_kwh = daily_savings_kwh * 365
        annual_savings_sgd = annual_savings_kwh * self.data['electricity_rate']
        
        return {
            'daily_savings_kwh': round(daily_savings_kwh, 2),
            'annual_savings_kwh': round(annual_savings_kwh, 2),
            'annual_savings_sgd': round(annual_savings_sgd, 2),
            'per_light_annual_savings': round(annual_savings_sgd / self.data['total_lights'], 2),
            'six_year_savings': round(annual_savings_sgd * 6, 2),
            'period_details': period_details,
            'original_daily_consumption': round(original_daily_consumption, 2),
            'smart_daily_consumption': round(smart_daily_consumption, 2)
        }

def main():
    # Inject Plausible analytics script
    st.components.v1.html(
        """
        <script defer data-domain="calculator.agranergy.com" src="https://plausible.io/js/script.js"></script>
        """,
        height=0
    )
    st.title('Agranergy Energy Savings Calculator')
    
    calculator = SmartLightingCalculator()
    
    # 初始化会话状态
    if 'step' not in st.session_state:
        st.session_state.step = 0
        st.session_state.data = {}
        st.session_state.calculator = calculator

    # 显示当前进度 (7 steps total)
    progress = st.progress(st.session_state.step / 7)
    
    # Display different questions based on steps
    if st.session_state.step == 0:
        st.write('Welcome to the Smart Lighting Energy Calculator! Let\'s collect some basic information.')
        project_name = st.text_input('Enter project name:')
        if st.button('Next') and project_name:
            st.session_state.calculator.data['project_name'] = project_name
            st.session_state.step += 1
            st.rerun()

    elif st.session_state.step == 1:
        st.write('Please tell me about your existing lighting system.')
        
        with st.form(key='lights_form'):
            total_lights = st.number_input('How many lights are there in total?', min_value=1, max_value=10000, value=500)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                previous_button = st.form_submit_button('Previous')
            with col2:
                next_button = st.form_submit_button('Next')
        
        if previous_button:
            st.session_state.step -= 1
            st.rerun()
            
        if next_button:
            valid, message = calculator.validate_input('total_lights', total_lights)
            if valid:
                st.session_state.calculator.data['total_lights'] = total_lights
                st.session_state.step += 1
                st.rerun()
            else:
                st.error(message)

    elif st.session_state.step == 2:
        st.write('Please provide the power information for existing lights.')
        
        with st.form(key='wattage_form'):
            original_wattage = st.number_input('What is the power of existing lights (W)?', min_value=1, max_value=400, value=18)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                previous_button = st.form_submit_button('Previous')
            with col2:
                next_button = st.form_submit_button('Next')
        
        if previous_button:
            st.session_state.step -= 1
            st.rerun()
            
        if next_button:
            if original_wattage < 10 or original_wattage > 200:
                st.error('This type of light is currently not supported in our calculator.')
            else:
                valid, message = calculator.validate_input('original_wattage', original_wattage)
                if valid:
                    st.session_state.calculator.data['original_wattage'] = original_wattage
                    # Set high power mode wattage based on input
                    high_wattage = st.session_state.calculator.calculate_high_brightness(original_wattage)
                    st.session_state.calculator.data['smart_light_high_wattage'] = high_wattage
                    st.session_state.calculator.data['smart_light_low_wattage'] = 2  # Fixed low power mode
                    st.session_state.step += 1
                    st.rerun()
                else:
                    st.error(message)

    elif st.session_state.step == 3:
        st.write('Please provide electricity rate information.')
        
        with st.form(key='rate_form'):
            electricity_rate = st.number_input('What is the electricity rate per kWh (SGD)?', min_value=0.1, max_value=1.0, step=0.1, value=0.3)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                previous_button = st.form_submit_button('Previous')
            with col2:
                next_button = st.form_submit_button('Next')
        
        if previous_button:
            st.session_state.step -= 1
            st.rerun()
            
        if next_button:
            valid, message = calculator.validate_input('electricity_rate', electricity_rate)
            if valid:
                st.session_state.calculator.data['electricity_rate'] = electricity_rate
                st.session_state.step += 1
                st.rerun()
            else:
                st.error(message)

    elif st.session_state.step == 4:
        st.session_state.step += 1
        st.rerun()

    elif st.session_state.step == 5:
        st.write('Set up the lighting schedule.')
        st.info('The total duration of all periods should add up to 24 hours. Times that cross midnight (e.g., 23:00-01:00) are handled automatically.')
        
        # Initialize periods in session state if not exists
        if 'periods' not in st.session_state:
            st.session_state.periods = 1
        
        def calculate_duration(start, end):
            # Convert times to minutes for calculation
            start_minutes = start.hour * 60 + start.minute
            end_minutes = end.hour * 60 + end.minute
            
            # Handle cases where end time is on the next day
            if end_minutes < start_minutes:
                end_minutes += 24 * 60
            
            # Return duration in hours
            return (end_minutes - start_minutes) / 60

        total_lights = st.session_state.calculator.data['total_lights']
        periods_data = []
        total_duration = 0
        
        col1, col2 = st.columns([3, 1])
        with col1:
            for i in range(st.session_state.periods):
                st.subheader(f'Period {i + 1}')
                
                # Default values for first period - 24h by default
                default_start = time(0, 0)
                default_end = time(23, 59) if i == 0 else time(0, 0)
                default_lights = total_lights if i == 0 else total_lights
                
                period_start = st.time_input(f'Start time for Period {i + 1}', default_start, key=f'start_{i}')
                period_end = st.time_input(f'End time for Period {i + 1}', default_end, key=f'end_{i}')
                duration = round(calculate_duration(period_start, period_end), 1)
                st.caption(f'Duration: {duration} hours')
                
                lights = st.number_input('Number of lights ON:', 
                                       min_value=0, 
                                       max_value=total_lights,
                                       value=default_lights,
                                       key=f'lights_{i}')
                
                periods_data.append({
                    'start': period_start,
                    'end': period_end,
                    'duration': duration,
                    'lights': lights
                })
                total_duration += duration
                st.divider()
        
        with col2:
            st.write('')
            st.write('')
            if st.session_state.periods < 5:
                if st.button('Add Period', key='add_period'):
                    st.session_state.periods += 1
                    st.rerun()
            
            if st.session_state.periods > 1:
                if st.button('Remove Period', key='remove_period'):
                    st.session_state.periods -= 1
                    st.rerun()
            
            st.write(f'Total Duration: {total_duration:.1f} hours')
            if abs(total_duration - 24) > 0.1:
                st.warning('Please adjust times to total 24 hours')

        if st.button('Next'):
            schedule = [
                {'duration': period['duration'], 'lights': period['lights']}
                for period in periods_data
            ]
            
            # Validate total hours
            if abs(total_duration - 24) > 0.1:  # Allow small rounding differences
                st.error(f'The total duration ({total_duration:.1f} hours) must be approximately 24 hours. Please adjust the time periods.')
            else:
                st.session_state.calculator.data['operation_schedule'] = schedule
                st.session_state.step += 1
                st.rerun()

    elif st.session_state.step == 6:
        st.write('Configure Smart Lighting Power Settings')
        st.info('Configure the power levels and operating mode ratios for the smart lighting system.')
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Power Levels')
            original_wattage = st.session_state.calculator.data['original_wattage']
            default_high_power = st.session_state.calculator.calculate_high_brightness(original_wattage)
            high_power = st.number_input('High Power Mode (W)', 
                                        min_value=5, 
                                        max_value=20, 
                                        value=default_high_power,
                                        help='Power consumption in high power mode')
            low_power = st.number_input('Low Power Mode (W)', 
                                       min_value=1, 
                                       max_value=5, 
                                       value=2,
                                       help='Power consumption in low power mode (default: 2W)')
        
        with col2:
            st.subheader('Operating Mode Ratio')
            st.caption('Adjust the percentage of time spent in high power mode')
            high_power_ratio = st.slider('High Power Mode Time (%)', 
                                        min_value=10, 
                                        max_value=50, 
                                        value=25,
                                        help='Percentage of time operating in high power mode') / 100
            st.caption(f'Low Power Mode Time: {(100 - high_power_ratio * 100):.0f}%')

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button('Previous'):
                st.session_state.step -= 1
                st.rerun()
        with col2:
            if st.button('Calculate Energy Savings'):
                st.session_state.calculator.data['smart_light_high_wattage'] = high_power
                st.session_state.calculator.data['smart_light_low_wattage'] = low_power
                st.session_state.calculator.data['high_power_ratio'] = high_power_ratio
                st.session_state.step += 1
                st.rerun()

    elif st.session_state.step == 7:
        # Display calculation results
        savings = st.session_state.calculator.calculate_savings()
        if savings:
            # Project Parameters Section
            st.subheader('Project Parameters')
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Total Lights: {st.session_state.calculator.data['total_lights']}")
                st.write(f"Original Wattage: {st.session_state.calculator.data['original_wattage']} W")
            with col2:
                st.write(f"Electricity Rate: {st.session_state.calculator.data['electricity_rate']} SGD/kWh")
                st.write(f"Smart Light High Power: {st.session_state.calculator.data['smart_light_high_wattage']} W")
            st.divider()

            # Key Metrics Section
            st.subheader('Key Energy Savings Metrics')
            metrics_cols = st.columns(4)
            with metrics_cols[0]:
                st.metric('Annual Energy Savings', f"{savings['annual_savings_kwh']:,.0f} kWh")
            with metrics_cols[1]:
                st.metric('Annual Cost Savings', f"SGD {savings['annual_savings_sgd']:,.0f}")
            with metrics_cols[2]:
                st.metric('6-Year Energy Savings', f"{savings['annual_savings_kwh']*6:,.0f} kWh")
            with metrics_cols[3]:
                st.metric('6-Year Cost Savings', f"SGD {savings['six_year_savings']:,.0f}")
            st.divider()

            # Proposals Section
            st.subheader('Investment Proposals')
            proposal_tabs = st.tabs(['Direct Purchase', 'EMC Contract'])

            # Direct Purchase Tab
            with proposal_tabs[0]:
                st.write('Parameters for Direct Purchase ROI:')
                dp_col1, dp_col2 = st.columns(2)
                with dp_col1:
                    light_price = st.number_input('Agranergy Light Tube Price (SGD)', value=85.0, step=1.0, key='dp_light_price')
                with dp_col2:
                    installation_cost = st.number_input('Installation Cost per Light (SGD)', value=5.0, step=1.0, key='dp_installation_cost')
                
                initial_investment = light_price * st.session_state.calculator.data['total_lights']
                total_installation = installation_cost * st.session_state.calculator.data['total_lights']
                roi = savings['six_year_savings'] - initial_investment - total_installation
                payback_period = (initial_investment + total_installation) / savings['annual_savings_sgd']

                st.write('Direct Purchase Analysis:')
                dp_metrics = st.columns(4)
                with dp_metrics[0]:
                    st.metric('Initial Investment', f"SGD {initial_investment:,.0f}")
                with dp_metrics[1]:
                    st.metric('Installation Cost', f"SGD {total_installation:,.0f}")
                with dp_metrics[2]:
                    st.metric('6-Year ROI', f"SGD {roi:,.0f}")
                with dp_metrics[3]:
                    st.metric('Payback Period', f"{payback_period:.1f} years")

            # EMC Contract Tab
            with proposal_tabs[1]:
                st.write('EMC Contract Parameters:')
                emc_col1, emc_col2, emc_col3 = st.columns(3)
                with emc_col1:
                    cost_share = st.number_input('Client Cost Saving Share (%)', value=60, min_value=0, max_value=100, key='emc_cost_share')
                with emc_col2:
                    placement_fee = st.number_input('Placement Fee per Light (SGD)', value=25.0, step=1.0, key='emc_placement_fee')
                with emc_col3:
                    emc_installation = st.number_input('Installation Cost per Light (SGD)', value=5.0, step=1.0, key='emc_installation_cost')

                total_placement = placement_fee * st.session_state.calculator.data['total_lights']
                total_emc_installation = emc_installation * st.session_state.calculator.data['total_lights']
                cost_saving_share = (cost_share / 100) * savings['six_year_savings']
                total_benefit = cost_saving_share - total_placement - total_emc_installation

                st.write('EMC Contract Analysis (6 years):')
                emc_metrics = st.columns(4)
                with emc_metrics[0]:
                    st.metric('Cost Saving Share', f"SGD {cost_saving_share:,.0f}")
                with emc_metrics[1]:
                    st.metric('Placement Fee', f"SGD {total_placement:,.0f}")
                with emc_metrics[2]:
                    st.metric('Installation Cost', f"SGD {total_emc_installation:,.0f}")
                with emc_metrics[3]:
                    st.metric('Total Benefit', f"SGD {total_benefit:,.0f}")
            
            st.divider()
            # Detailed Calculations Section
            with st.expander('View Detailed Calculations'):
                # System Comparison
                st.subheader('System Consumption Comparison')
                comp_cols = st.columns(2)
                with comp_cols[0]:
                    st.write('Original System:')
                    st.metric('Daily Consumption', f"{savings['original_daily_consumption']:,.1f} kWh")
                    st.metric('Annual Consumption', f"{savings['original_daily_consumption']*365:,.0f} kWh")
                    st.metric('Annual Cost', f"SGD {savings['original_daily_consumption']*365*st.session_state.calculator.data['electricity_rate']:,.0f}")
                with comp_cols[1]:
                    st.write('Smart System:')
                    st.metric('Daily Consumption', f"{savings['smart_daily_consumption']:,.1f} kWh")
                    st.metric('Annual Consumption', f"{savings['smart_daily_consumption']*365:,.0f} kWh")
                    st.metric('Annual Cost', f"SGD {savings['smart_daily_consumption']*365*st.session_state.calculator.data['electricity_rate']:,.0f}")
                
                st.divider()
                st.subheader('Period Details')
                # Create a DataFrame for the period details
                df = pd.DataFrame(savings['period_details'])
                df.columns = ['Period', 'Lights ON', 'Original Consumption (kWh)', 
                             'High Power Hours', 'Low Power Hours',
                             'High Power Consumption (kWh)', 'Low Power Consumption (kWh)',
                             'Smart Total Consumption (kWh)', 'Period Savings (kWh)']
                
                # Format numeric columns with comma separators
                numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
                for col in numeric_columns:
                    if col == 'Lights ON':
                        df[col] = df[col].apply(lambda x: f'{int(x):,}')
                    else:
                        df[col] = df[col].apply(lambda x: f'{x:,.2f}')
                
                # Display the detailed table with index starting from 1
                df.index = range(1, len(df) + 1)
                st.dataframe(df, use_container_width=True)

            # Add PDF export functionality
            if st.button('Export Results to PDF'):
                pdf_buffer = io.BytesIO()
                # Use A4 landscape with larger margins for better readability
                doc = SimpleDocTemplate(
                    pdf_buffer,
                    pagesize=landscape(letter),
                    leftMargin=50,
                    rightMargin=50,
                    topMargin=50,
                    bottomMargin=50
                )
                elements = []
                styles = getSampleStyleSheet()
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=24,
                    spaceAfter=30,
                    alignment=1
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=16,
                    spaceAfter=20,
                    spaceBefore=20,
                    alignment=1
                )
                normal_style = ParagraphStyle(
                    'Normal',
                    parent=styles['Normal'],
                    fontSize=12,
                    spaceBefore=10,
                    spaceAfter=10
                )

                # Add title and project name
                elements.append(Paragraph(f"Agranergy Energy Savings Report - {st.session_state.calculator.data['project_name']}", title_style))
                elements.append(Spacer(1, 20))

                # Project Parameters
                elements.append(Paragraph("Project Parameters", subtitle_style))
                project_data = [
                    ["Parameter", "Value"],
                    ["Total Lights", f"{st.session_state.calculator.data['total_lights']:,}"],
                    ["Original Wattage", f"{st.session_state.calculator.data['original_wattage']}W"],
                    ["Electricity Rate", f"SGD {st.session_state.calculator.data['electricity_rate']}/kWh"],
                    ["Smart Light High Power", f"{st.session_state.calculator.data['smart_light_high_wattage']}W"],
                    ["Smart Light Low Power", f"{st.session_state.calculator.data['smart_light_low_wattage']}W"]
                ]
                t = Table(project_data, colWidths=[200, 200])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

                # Key Energy Savings Metrics
                elements.append(Paragraph("Key Energy Savings Metrics", subtitle_style))
                metrics_data = [
                    ["Metric", "Value"],
                    ["Annual Energy Savings", f"{savings['annual_savings_kwh']:,.0f} kWh"],
                    ["Annual Cost Savings", f"SGD {savings['annual_savings_sgd']:,.0f}"],
                    ["6-Year Energy Savings", f"{savings['annual_savings_kwh']*6:,.0f} kWh"],
                    ["6-Year Cost Savings", f"SGD {savings['six_year_savings']:,.0f}"]
                ]
                t = Table(metrics_data, colWidths=[200, 200])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

                # Direct Purchase Analysis
                elements.append(Paragraph("Direct Purchase Analysis", subtitle_style))
                dp_data = [
                    ["Parameter", "Value"],
                    ["Light Tube Price", f"SGD {light_price:,.2f}"],
                    ["Installation Cost", f"SGD {installation_cost:,.2f}"],
                    ["Initial Investment", f"SGD {initial_investment:,.0f}"],
                    ["Total Installation Cost", f"SGD {total_installation:,.0f}"],
                    ["6-Year ROI", f"SGD {roi:,.0f}"],
                    ["Payback Period", f"{payback_period:.1f} years"]
                ]
                t = Table(dp_data, colWidths=[200, 200])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

                # EMC Contract Analysis
                elements.append(Paragraph("EMC Contract Analysis (6 years)", subtitle_style))
                emc_data = [
                    ["Parameter", "Value"],
                    ["Client Cost Saving Share", f"{cost_share}%"],
                    ["Placement Fee per Light", f"SGD {placement_fee:,.2f}"],
                    ["Installation Cost per Light", f"SGD {emc_installation:,.2f}"],
                    ["Total Cost Saving Share", f"SGD {cost_saving_share:,.0f}"],
                    ["Total Placement Fee", f"SGD {total_placement:,.0f}"],
                    ["Total Installation Cost", f"SGD {total_emc_installation:,.0f}"],
                    ["Total Benefit", f"SGD {total_benefit:,.0f}"]
                ]
                t = Table(emc_data, colWidths=[200, 200])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))

                # System Comparison
                elements.append(Paragraph("System Consumption Comparison", subtitle_style))
                comparison_data = [
                    ["Metric", "Original System", "Smart System"],
                    ["Daily Consumption", f"{savings['original_daily_consumption']:,.1f} kWh", f"{savings['smart_daily_consumption']:,.1f} kWh"],
                    ["Annual Consumption", f"{savings['original_daily_consumption']*365:,.0f} kWh", f"{savings['smart_daily_consumption']*365:,.0f} kWh"],
                    ["Annual Cost", f"SGD {savings['original_daily_consumption']*365*st.session_state.calculator.data['electricity_rate']:,.0f}", 
                     f"SGD {savings['smart_daily_consumption']*365*st.session_state.calculator.data['electricity_rate']:,.0f}"]
                ]
                t = Table(comparison_data, colWidths=[133, 133, 134])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 30))

                # Add period details table
                elements.append(Paragraph("Detailed Calculations by Period", subtitle_style))
                elements.append(Spacer(1, 20))

                # Create period details table
                period_headers = [
                    'Period',
                    'Lights ON (%)',
                    'Original (kWh)',
                    'High Power (kWh)',
                    'Low Power (kWh)',
                    'Smart Total (kWh)',
                    'Savings (kWh)'
                ]
                
                period_data = [period_headers]
                for period in savings['period_details']:
                    period_data.append([
                        period['period'],
                        period['lights_on'],
                        f"{period['original_consumption']:,.2f}",
                        f"{period['smart_high_consumption']:,.2f}",
                        f"{period['smart_low_consumption']:,.2f}",
                        f"{period['smart_total_consumption']:,.2f}",
                        f"{period['period_savings']:,.2f}"
                    ])
                
                # Calculate column widths for better fit
                col_widths = [100, 80, 90, 90, 90, 90, 90]
                t = Table(period_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(t)

                # Add page numbers to PDF
                def add_page_number(canvas, doc):
                    canvas.saveState()
                    canvas.setFont('Helvetica', 9)
                    canvas.drawRightString(
                        doc.pagesize[0] - 50,
                        50,
                        f"Page {doc.page}"
                    )
                    canvas.restoreState()

                # Build PDF with page numbers
                doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
                pdf_data = pdf_buffer.getvalue()
                pdf_buffer.close()

                # Offer the PDF for download
                st.download_button(
                    label='Download PDF Report',
                    data=pdf_data,
                    file_name=f'energy_savings_report_{st.session_state.calculator.data["project_name"]}.pdf',
                    mime='application/pdf'
                )

            # Add reset button
            if st.button('Calculate Again'):
                st.session_state.step = 0
                st.rerun()
        else:
            st.error('Error in calculations. Please check your input data.')

if __name__ == '__main__':
    main()