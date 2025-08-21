# Recurring Tasks Feature - User Guide

## Overview

The recurring tasks feature allows team members to automatically receive daily and weekly tasks based on their preferences. This system provides flexibility for team members to choose which recurring tasks they want to participate in, while giving administrators full control over task templates.

## Key Features

### 1. **Flexible Recurring Patterns**
- **Daily Tasks**: Automatically created every day
- **Weekly Tasks**: Created on specific days of the week
- **Both**: Tasks that can be both daily and weekly
- **Member Choice**: Team members can opt-in/opt-out of recurring tasks
- **Automatic Assignment**: Tasks assigned to all members or specific users

### 2. **Smart Instance Management**
- Each recurring task creates separate instances
- Instances are dated and tracked individually
- No duplicate instances for the same date/user
- Completion of one instance doesn't affect others

### 3. **Admin Controls**
- Create and manage recurring task templates
- Set recurrence patterns and days
- Control member selection permissions
- Monitor usage statistics
- Manual task generation

## How to Use

### For Team Members

#### Accessing Recurring Tasks
1. Go to **Tasks** → **Recurring Tasks** (from the main task list)
2. Browse available recurring task templates
3. Choose daily or weekly participation for each task

#### Selecting Daily Tasks
1. Find a task you want to do daily
2. Click **"Select Daily"** button
3. The task will be automatically created for you each day
4. Click the green **"Selected Daily"** button to deselect

#### Selecting Weekly Tasks
1. Find a task for weekly participation
2. Select the days of the week you want the task
3. Click **"Update Weekly Selection"**
4. Tasks will be created on your selected days
5. Use the **"Remove"** button to stop weekly tasks

#### Completing Recurring Task Instances
- Recurring task instances appear in your regular task list
- Complete them like any normal task
- Each completion earns points as specified in the template
- Completed instances don't regenerate

### For Administrators

#### Creating Recurring Task Templates
1. Go to **Tasks** → **Templates** (admin button in task list)
2. Click **"Create Template"**
3. Fill in the template details:

**Basic Information:**
- **Title**: Clear, descriptive name
- **Description**: What the task involves
- **Category**: Optional task category

**Task Properties:**
- **Type**: Feature, Bug Fix, Learning, etc.
- **Priority**: Low to Critical
- **Difficulty**: Easy to Expert
- **Estimated Hours**: Time expected per instance
- **Points Value**: Points awarded per completion

**Recurrence Settings:**
- **Type**: Daily, Weekly, or Both
- **Days**: For weekly tasks, select specific days
- **Member Selection**: Allow team members to choose
- **Auto-assign**: Automatically assign to all members

**Completion Criteria:**
- **Acceptance Criteria**: What constitutes completion

#### Managing Templates
1. View all templates in **Tasks** → **Templates**
2. See statistics for each template:
   - Daily selections count
   - Weekly selections count
   - Total instances created
3. Edit templates by clicking **"Edit"**
4. View template details with **"View"**

#### Generating Tasks
**Automatic Generation:**
- Set up a daily cron job: `python manage.py generate_recurring_tasks`
- Tasks are generated automatically at midnight

**Manual Generation:**
- Use the **"Generate Today's Tasks"** button in Templates
- Or run: `python manage.py generate_recurring_tasks`
- For specific dates: `python manage.py generate_recurring_tasks --date 2025-08-21`
- For multiple days: `python manage.py generate_recurring_tasks --days-ahead 7`

## Best Practices

### For Template Creation
1. **Clear Titles**: Use descriptive names like "Daily Standup Notes" or "Weekly Code Review"
2. **Realistic Time Estimates**: Set achievable time expectations
3. **Appropriate Points**: Match points to effort and importance
4. **Detailed Descriptions**: Explain what's expected clearly
5. **Flexible Scheduling**: Consider team schedules when setting weekly days

### For Team Members
1. **Start Small**: Begin with 1-2 recurring tasks to avoid overwhelm
2. **Regular Review**: Adjust your selections based on workload
3. **Consistent Completion**: Try to complete recurring tasks regularly
4. **Communicate**: Let team leads know if recurring tasks aren't working

### For Team Management
1. **Monitor Participation**: Check template statistics regularly
2. **Adjust Based on Feedback**: Modify templates based on team input
3. **Seasonal Adjustments**: Update recurring tasks for different project phases
4. **Backup Generation**: Ensure the daily generation command runs reliably

## Technical Details

### Database Structure
- **Task Model**: Extended with recurring fields
- **TaskRecurringSelection**: Tracks member choices
- **Template Tasks**: Special tasks with `is_template=True`
- **Instance Tasks**: Generated from templates with `template_task` reference

### API Integration
- All recurring task functions are available through Django admin
- Management commands for automated generation
- Web interface for user selections
- Statistics tracking for analytics

### Automation Setup
Add to your cron jobs (Linux/Mac) or Task Scheduler (Windows):
```bash
# Run daily at midnight
0 0 * * * cd /path/to/project && python manage.py generate_recurring_tasks
```

## Troubleshooting

### Common Issues

**Tasks not generating:**
- Check that templates have `is_template=True` and `is_recurring=True`
- Verify users have made selections
- Ensure the generation command runs without errors

**Duplicate tasks:**
- The system prevents duplicates automatically
- If duplicates appear, check for concurrent generation runs

**Missing selections:**
- Verify users are authenticated when making selections
- Check TaskRecurringSelection records in admin

**Performance issues:**
- Monitor the number of active recurring tasks
- Consider archiving old completed instances
- Optimize generation for large teams

### Support
For technical issues:
1. Check Django admin for TaskRecurringSelection records
2. Review server logs during task generation
3. Test generation command manually with verbose output:
   ```bash
   python manage.py generate_recurring_tasks --verbosity 2
   ```

## Examples

### Example Daily Task Template
- **Title**: "Daily Progress Update"
- **Description**: "Submit a brief update on your daily progress and blockers"
- **Type**: Learning
- **Priority**: Medium
- **Points**: 5
- **Recurrence**: Daily
- **Member Selection**: Enabled

### Example Weekly Task Template
- **Title**: "Weekly Code Review"
- **Description**: "Review and comment on team code submissions"
- **Type**: Feature
- **Priority**: High
- **Points**: 20
- **Recurrence**: Weekly (Monday, Wednesday, Friday)
- **Member Selection**: Enabled

This feature enhances team productivity by automating routine task creation while maintaining flexibility for individual preferences.
