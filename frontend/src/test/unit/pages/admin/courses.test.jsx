import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { message } from 'antd';
import AdminCourses from '../../../../pages/admin/courses';

jest.spyOn(message, 'success').mockImplementation(() => {});
jest.spyOn(message, 'error').mockImplementation(() => {});

beforeAll(() => {
  if (!window.matchMedia) {
    window.matchMedia = () => ({
      matches: false,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    });
  }
});

const jsonResponse = (body, ok = true, status = 200) =>
  Promise.resolve({ ok, status, json: () => Promise.resolve(body) });

const COURSES = [
  { id: 'course-1', name: 'CS 101', semester: 'Fall', year: '2026', instructor_id: 'i1', vertex_enabled: false },
];

function mockFetch({ toggleOk = true } = {}) {
  global.fetch = jest.fn((url) => {
    if (url.includes('/get_all_courses')) return jsonResponse(COURSES);
    if (url.includes('/get_user_by_id')) return jsonResponse({ name: 'Prof X' });
    if (url.includes('/admin_set_course_vertex')) {
      return toggleOk
        ? jsonResponse({ course_id: 'course-1', vertex_enabled: true })
        : jsonResponse({ message: 'nope' }, false, 403);
    }
    return jsonResponse({}, false, 404);
  });
}

const renderPage = () =>
  render(
    <MemoryRouter>
      <AdminCourses />
    </MemoryRouter>
  );

describe('<AdminCourses /> Vertex AI toggle', () => {
  afterEach(() => {
    message.success.mockClear();
    message.error.mockClear();
  });

  it('shows the current Vertex AI state for each course', async () => {
    mockFetch();
    renderPage();

    const toggle = await screen.findByRole('switch', { name: /vertex ai for cs 101/i });
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('enables Vertex AI for a course with a credentialed PUT', async () => {
    mockFetch();
    renderPage();

    const toggle = await screen.findByRole('switch', { name: /vertex ai for cs 101/i });
    fireEvent.click(toggle);

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'));
    const [url, options] = global.fetch.mock.calls.find(([u]) =>
      u.includes('/admin_set_course_vertex')
    );
    expect(url).toContain('/admin_set_course_vertex');
    expect(options.method).toBe('PUT');
    expect(options.credentials).toBe('include');
    expect(JSON.parse(options.body)).toEqual({ course_id: 'course-1', enabled: true });
    expect(message.success).toHaveBeenCalled();
  });

  it('leaves the switch off and shows an error when the update fails', async () => {
    mockFetch({ toggleOk: false });
    renderPage();

    const toggle = await screen.findByRole('switch', { name: /vertex ai for cs 101/i });
    fireEvent.click(toggle);

    await waitFor(() => expect(message.error).toHaveBeenCalled());
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });
});
