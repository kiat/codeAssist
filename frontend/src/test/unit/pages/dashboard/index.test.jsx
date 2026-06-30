import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import Dashboard from '../../../../pages/dashboard';
import { GlobalContext } from '../../../../App';

jest.mock('antd', () => {
  const real  = jest.requireActual('antd');
  const React = require('react');
  const PageHeader = ({ title }) => <h1>{title}</h1>;
  const message    = { success: jest.fn(), error: jest.fn() };
  return { ...real, PageHeader, message };
});

jest.mock(
  '../../../../pages/dashboard/semesterCourses',
  () => {
    const React = require('react');
    const mockSemesterCourses = jest.fn(({ courses, toggleModal }) => (
      <div data-testid="semester-courses">
        <button onClick={toggleModal}>Add course</button>
        <pre data-testid="courses-prop">{JSON.stringify(courses)}</pre>
      </div>
    ));
    return { __esModule: true, default: mockSemesterCourses };
  }
);

jest.mock(
  '../../../../pages/dashboard/courseModal',
  () => {
    const React = require('react');
    const mockCourseModal = jest.fn(({ open, children }) =>
      open ? <div data-testid="course-modal">{children}</div> : null
    );
    return { __esModule: true, default: mockCourseModal };
  }
);

jest.mock(
  '../../../../pages/dashboard/addForm',
  () => {
    const React = require('react');
    const mockAddForm = jest.fn(({ onFinish }) => (
      <div data-testid="add-form">
        <button
          onClick={() =>
            onFinish({
              courseName: 'CS102',
              year: '2025',
              semester: 'Fall',
              entryCode: 'NEWCODE',
            })
          }
        >
          Submit AddForm
        </button>
      </div>
    ));
    return { __esModule: true, default: mockAddForm };
  }
);

jest.mock(
  '../../../../pages/dashboard/relationForm',
  () => ({ __esModule: true, default: () => <div>relation-form</div> })
);

jest.mock(
  '../../../../services/course',
  () => ({
    getUserEnrollments : jest.fn(),
    getCourseAssignments: jest.fn(),
    createCourse       : jest.fn(),
    enrollCourse       : jest.fn(),
  })
);
const {
  getUserEnrollments,
  getCourseAssignments,
  createCourse,
} = require('../../../../services/course');

const { default: mockSemesterCourses }   =
  require('../../../../pages/dashboard/semesterCourses');

beforeEach(() => {
  jest.clearAllMocks();

  getUserEnrollments.mockResolvedValue({
    data: [
      {
        id: 1,
        name: 'Intro CS',
        description: 'Basics',
        semester: 'Fall',
        year: '2025',
      },
    ],
  });
  getCourseAssignments.mockResolvedValue({ data: [{}, {}] }); // two per course
  createCourse.mockResolvedValue({});
});

describe('<Dashboard />', () => {
  const ctxValue = { userInfo: { id: 42, isStudent: false } };

  it('loads courses, opens modal, submits form, refetches', async () => {
    render(
      <GlobalContext.Provider value={ctxValue}>
        <Dashboard />
      </GlobalContext.Provider>
    );

      await waitFor(() => {
        const coursesObj = JSON.parse(
          screen.getByTestId('courses-prop').textContent || '{}'
        );
        expect(coursesObj['2025Fall']?.[0]).toMatchObject({
          name: 'Intro CS',
          assignments: 2,
        });
      });

    await userEvent.click(screen.getByRole('button', { name: /add course/i }));
    expect(screen.getByTestId('course-modal')).toBeInTheDocument();


    await userEvent.click(screen.getByRole('button', { name: /submit addform/i }));

    await waitFor(() =>
      expect(createCourse).toHaveBeenCalledWith({
        name: 'CS102',
        instructor_id: 42,
        semester: 'Fall',
        year: '2025',
        entryCode: 'NEWCODE',
      })
    );

    expect(getUserEnrollments).toHaveBeenCalledTimes(3); 
  });
});

