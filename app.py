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
            st.success('Calculation complete! Here are the energy saving results:')
            
            col1, col2 = st.columns(2)
            # Round all savings values to 2 decimal places
            savings = {k: round(v, 2) if isinstance(v, (int, float)) and k != 'period_details' else v 
                      for k, v in savings.items()}
            
            with col1:
                st.metric('Annual Energy Savings', f"{savings['annual_savings_kwh']:,.0f} kWh")
                st.metric('Annual Cost Savings', f"SGD {savings['annual_savings_sgd']:,.0f}")
                st.metric('Annual Savings per Light', f"SGD {savings['per_light_annual_savings']:,.0f}")
            with col2:
                st.metric('6-Year Total Savings', f"SGD {savings['six_year_savings']:,.0f}")
                st.metric('Daily Energy Savings', f"{savings['daily_savings_kwh']:,.1f} kWh")

            # Display detailed calculations table
            st.subheader('Detailed Calculations')
            
            # Create a DataFrame for the period details and round numeric columns
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

            # Summary table
            st.subheader('Daily Summary')
            summary_data = {
                'System': ['Original System', 'Smart Lighting System'],
                'Daily Consumption (kWh)': [savings['original_daily_consumption'], 
                                          savings['smart_daily_consumption']],
                'Annual Consumption (kWh)': [savings['original_daily_consumption'] * 365, 
                                           savings['smart_daily_consumption'] * 365],
                'Annual Cost (SGD)': [
                    savings['original_daily_consumption'] * 365 * st.session_state.calculator.data['electricity_rate'],
                    savings['smart_daily_consumption'] * 365 * st.session_state.calculator.data['electricity_rate']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            
            # Format numeric columns with comma separators
            numeric_columns = ['Daily Consumption (kWh)', 'Annual Consumption (kWh)', 'Annual Cost (SGD)']
            for col in numeric_columns:
                summary_df[col] = summary_df[col].apply(lambda x: f'{x:,.2f}')
            
            summary_df.index = range(1, len(summary_df) + 1)
            st.dataframe(summary_df, use_container_width=True)

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
                    alignment=1  # Center alignment
                )
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Heading2'],
                    fontSize=16,
                    spaceAfter=20,
                    spaceBefore=20,
                    alignment=1  # Center alignment
                )

                # Add title
                elements.append(Paragraph(f"Agranergy Energy Savings Report - {st.session_state.calculator.data['project_name']}", title_style))
                elements.append(Spacer(1, 20))

                # Add project details
                elements.append(Paragraph("Project Details", subtitle_style))
                project_data = [
                    ["Parameter", "Value"],
                    ["Total Lights", st.session_state.calculator.data['total_lights']],
                    ["Original Wattage", f"{st.session_state.calculator.data['original_wattage']}W"],
                    ["Electricity Rate", f"SGD {st.session_state.calculator.data['electricity_rate']}/kWh"],
                    ["Smart Light High Power", "10W"],
                    ["Smart Light Low Power", "2W"]
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

                # Add savings summary
                elements.append(Paragraph("Savings Summary", subtitle_style))
                summary_data = [
                    ["Metric", "Value"],
                    ["Annual Energy Savings", f"{savings['annual_savings_kwh']} kWh"],
                    ["Annual Cost Savings", f"SGD {savings['annual_savings_sgd']}"],
                    ["Annual Savings per Light", f"SGD {savings['per_light_annual_savings']}"],
                    ["6-Year Total Savings", f"SGD {savings['six_year_savings']}"],
                    ["Daily Energy Savings", f"{savings['daily_savings_kwh']} kWh"]
                ]
                t = Table(summary_data, colWidths=[200, 200])
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

                # Add period details table with more spacing and adjusted layout
                elements.append(Spacer(1, 40))  # Add more space before the table
                elements.append(Paragraph("Detailed Calculations by Period", subtitle_style))
                elements.append(Spacer(1, 20))  # Add space between title and table
                
                # Rename and reorder columns for better readability
                df.columns = [
                    'Period',
                    'Lights ON',
                    'Original (kWh)',
                    'High Hours',
                    'Low Hours',
                    'High Power (kWh)',
                    'Low Power (kWh)',
                    'Smart Total (kWh)',
                    'Savings (kWh)'
                ]
                
                # Round numeric values in the DataFrame
                numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns
                df[numeric_columns] = df[numeric_columns].round(2)
                
                period_data = [[col for col in df.columns]] + df.values.tolist()
                # Adjust column widths for better fit
                col_widths = [90, 70, 90, 70, 70, 90, 90, 90, 90]
                t = Table(period_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),  # Slightly smaller font
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),  # Slightly smaller font
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),  # Add padding
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)  # Add padding
                ]))
                elements.append(t)
                elements.append(Spacer(1, 20))  # Add space after table

                # Build PDF with page numbers
                def add_page_number(canvas, doc):
                    canvas.saveState()
                    canvas.setFont('Helvetica', 9)
                    canvas.drawRightString(
                        doc.pagesize[0] - 50,
                        50,
                        f"Page {doc.page}"
                    )
                    canvas.restoreState()

                doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
                pdf_bytes = pdf_buffer.getvalue()
                st.download_button(
                    label='Download PDF Report',
                    data=pdf_bytes,
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