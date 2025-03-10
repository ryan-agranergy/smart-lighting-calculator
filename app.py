import streamlit as st
import openai
from datetime import datetime, time
import os
from dotenv import load_dotenv
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class SmartLightingCalculator:
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

            # Store period details
            period_details.append({
                'period': f"{period['duration']} hours",
                'lights_on': lights_on,
                'original_consumption': period_original,
                'smart_high_hours': high_hours if lights_on > 0 else 0,  # Only count hours if lights are on
                'smart_low_hours': low_hours if lights_on > 0 else 0,   # Only count hours if lights are on
                'smart_high_consumption': period_high,
                'smart_low_consumption': period_low,
                'smart_total_consumption': period_smart,
                'period_savings': period_original - period_smart
            })

        # Calculate total savings
        daily_savings_kwh = original_daily_consumption - smart_daily_consumption
        annual_savings_kwh = daily_savings_kwh * 365
        annual_savings_sgd = annual_savings_kwh * self.data['electricity_rate']
        
        return {
            'daily_savings_kwh': daily_savings_kwh,
            'annual_savings_kwh': annual_savings_kwh,
            'annual_savings_sgd': annual_savings_sgd,
            'per_light_annual_savings': annual_savings_sgd / self.data['total_lights'],
            'six_year_savings': annual_savings_sgd * 6,
            'period_details': period_details,
            'original_daily_consumption': original_daily_consumption,
            'smart_daily_consumption': smart_daily_consumption
        }

def main():
    st.set_page_config(page_title='Smart Lighting Energy Calculator', layout='wide')
    st.title('Smart Lighting Energy Calculator')
    
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
            st.experimental_rerun()

    elif st.session_state.step == 1:
        st.write('Please tell me about your existing lighting system.')
        total_lights = st.number_input('How many lights are there in total?', min_value=1, max_value=10000, value=500)
        if st.button('Next') and total_lights:
            valid, message = calculator.validate_input('total_lights', total_lights)
            if valid:
                st.session_state.calculator.data['total_lights'] = total_lights
                st.session_state.step += 1
                st.experimental_rerun()
            else:
                st.error(message)

    elif st.session_state.step == 2:
        st.write('Please provide the power information for existing lights.')
        original_wattage = st.number_input('What is the power of existing lights (W)?', min_value=1, max_value=400, value=30)
        if st.button('Next') and original_wattage:
            valid, message = calculator.validate_input('original_wattage', original_wattage)
            if valid:
                st.session_state.calculator.data['original_wattage'] = original_wattage
                st.session_state.step += 1
                st.experimental_rerun()
            else:
                st.error(message)

    elif st.session_state.step == 3:
        st.write('Please provide electricity rate information.')
        electricity_rate = st.number_input('What is the electricity rate per kWh (SGD)?', min_value=0.1, max_value=1.0, step=0.1, value=0.5)
        if st.button('Next') and electricity_rate:
            valid, message = calculator.validate_input('electricity_rate', electricity_rate)
            if valid:
                st.session_state.calculator.data['electricity_rate'] = electricity_rate
                st.session_state.step += 1
                st.experimental_rerun()
            else:
                st.error(message)

    elif st.session_state.step == 4:
        st.session_state.step += 1
        st.experimental_rerun()

    elif st.session_state.step == 5:
        st.write('Set up the lighting schedule.')
        st.write('Please configure the three time periods and the number of lights for each period:')
        st.info('The total duration of all periods should add up to 24 hours. Times that cross midnight (e.g., 23:00-01:00) are handled automatically.')
        
        col1, col2 = st.columns(2)
        with col1:
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
            # Calculate default values (rounded to nearest 10)
            default_period1 = total_lights  # 100% of lights
            default_period2 = round(total_lights * 0.5 / 10) * 10  # 50% of lights
            default_period3 = round(total_lights * 0.25 / 10) * 10  # 25% of lights
            
            st.subheader('Period 1')
            st.caption('e.g. Peak hours with full lighting')
            period1_start = st.time_input('Start time for Period 1', time(8, 0))
            period1_end = st.time_input('End time for Period 1', time(23, 0))
            duration1 = calculate_duration(period1_start, period1_end)
            st.caption(f'Duration: {duration1:.1f} hours')
            lights_period1 = st.number_input('Number of lights ON:', 
                                           min_value=0, 
                                           max_value=total_lights,
                                           value=default_period1,
                                           key='lights1')
            
            st.subheader('Period 2')
            st.caption('e.g. Evening hours with reduced lighting')
            period2_start = st.time_input('Start time for Period 2', time(23, 0))
            period2_end = st.time_input('End time for Period 2', time(1, 0))
            duration2 = calculate_duration(period2_start, period2_end)
            st.caption(f'Duration: {duration2:.1f} hours')
            lights_period2 = st.number_input('Number of lights ON:', 
                                           min_value=0, 
                                           max_value=total_lights,
                                           value=default_period2,
                                           key='lights2')
            
            st.subheader('Period 3')
            st.caption('e.g. Night hours with minimum lighting')
            period3_start = st.time_input('Start time for Period 3', time(1, 0))
            period3_end = st.time_input('End time for Period 3', time(8, 0))
            duration3 = calculate_duration(period3_start, period3_end)
            st.caption(f'Duration: {duration3:.1f} hours')
            lights_period3 = st.number_input('Number of lights ON:', 
                                           min_value=0, 
                                           max_value=total_lights,
                                           value=default_period3,
                                           key='lights3')
            
            total_duration = duration1 + duration2 + duration3
            if abs(total_duration - 24) > 0.1:
                st.warning(f'Total duration: {total_duration:.1f} hours. Please adjust the times to total 24 hours.')

        if st.button('Next'):
            # Calculate durations
            duration1 = calculate_duration(period1_start, period1_end)
            duration2 = calculate_duration(period2_start, period2_end)
            duration3 = calculate_duration(period3_start, period3_end)
            
            schedule = [
                {'duration': duration1, 'lights': lights_period1},
                {'duration': duration2, 'lights': lights_period2},
                {'duration': duration3, 'lights': lights_period3}
            ]
            
            # Validate total hours
            total_hours = sum(period['duration'] for period in schedule)
            if abs(total_hours - 24) > 0.1:  # Allow small rounding differences
                st.error(f'The total duration ({total_hours:.1f} hours) must be approximately 24 hours. Please adjust the time periods.')
            else:
                st.session_state.calculator.data['operation_schedule'] = schedule
                st.session_state.step += 1
                st.experimental_rerun()

    elif st.session_state.step == 6:
        st.write('Configure Smart Lighting Power Settings')
        st.info('Configure the power levels and operating mode ratios for the smart lighting system.')
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader('Power Levels')
            high_power = st.number_input('High Power Mode (W)', 
                                        min_value=5, 
                                        max_value=20, 
                                        value=10,
                                        help='Power consumption in high power mode (default: 10W)')
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

        if st.button('Calculate Energy Savings'):
            st.session_state.calculator.data['smart_light_high_wattage'] = high_power
            st.session_state.calculator.data['smart_light_low_wattage'] = low_power
            st.session_state.calculator.data['high_power_ratio'] = high_power_ratio
            st.session_state.step += 1
            st.experimental_rerun()

    elif st.session_state.step == 7:
        # Display calculation results
        savings = st.session_state.calculator.calculate_savings()
        if savings:
            st.success('Calculation complete! Here are the energy saving results:')
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric('Annual Energy Savings', f"{savings['annual_savings_kwh']:.2f} kWh")
                st.metric('Annual Cost Savings', f"SGD {savings['annual_savings_sgd']:.2f}")
                st.metric('Annual Savings per Light', f"SGD {savings['per_light_annual_savings']:.2f}")
            with col2:
                st.metric('6-Year Total Savings', f"SGD {savings['six_year_savings']:.2f}")
                st.metric('Daily Energy Savings', f"{savings['daily_savings_kwh']:.2f} kWh")

            # Display detailed calculations table
            st.subheader('Detailed Calculations')
            
            # Create a DataFrame for the period details
            df = pd.DataFrame(savings['period_details'])
            df.columns = ['Period', 'Lights ON', 'Original Consumption (kWh)', 
                         'High Power Hours', 'Low Power Hours',
                         'High Power Consumption (kWh)', 'Low Power Consumption (kWh)',
                         'Smart Total Consumption (kWh)', 'Period Savings (kWh)']
            
            # Display the detailed table
            st.dataframe(df)

            # Summary table
            st.subheader('Daily Summary')
            summary_data = {
                'System': ['Original System', 'Smart Lighting System'],
                'Daily Consumption (kWh)': [savings['original_daily_consumption'], savings['smart_daily_consumption']],
                'Annual Consumption (kWh)': [savings['original_daily_consumption'] * 365, savings['smart_daily_consumption'] * 365],
                'Annual Cost (SGD)': [
                    savings['original_daily_consumption'] * 365 * st.session_state.calculator.data['electricity_rate'],
                    savings['smart_daily_consumption'] * 365 * st.session_state.calculator.data['electricity_rate']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df)

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
                elements.append(Paragraph(f"Energy Savings Report - {st.session_state.calculator.data['project_name']}", title_style))
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
                    ["Annual Energy Savings", f"{savings['annual_savings_kwh']:.2f} kWh"],
                    ["Annual Cost Savings", f"SGD {savings['annual_savings_sgd']:.2f}"],
                    ["Annual Savings per Light", f"SGD {savings['per_light_annual_savings']:.2f}"],
                    ["6-Year Total Savings", f"SGD {savings['six_year_savings']:.2f}"],
                    ["Daily Energy Savings", f"{savings['daily_savings_kwh']:.2f} kWh"]
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
                st.experimental_rerun()
        else:
            st.error('Error in calculations. Please check your input data.')

if __name__ == '__main__':
    main()