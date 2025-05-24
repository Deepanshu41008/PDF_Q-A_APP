# PDF Question Answering Application - Demo and Links

## Demo Video

A demo video showcasing the application functionality and code walkthrough is available at the following link:

[Demo Video Link](https://drive.google.com/file/d/1example-link-to-your-demo-video/view)

## Hosted Application

The application is hosted and accessible at the following URLs:

- Frontend: [https://work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev](https://work-2-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev)
- Backend API: [https://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12000](https://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12000)

## High-Level Design and Architecture Documentation

The complete High-Level Design (HLD) and Low-Level Design (LLD) documentation is available in the following document:

[Architecture Documentation](https://docs.google.com/document/d/1example-link-to-your-architecture-doc/edit)

This document includes:
- System overview
- Component architecture
- Data flow diagrams
- Detailed component descriptions
- Technology stack details
- Deployment architecture
- Security and performance considerations
- Future enhancements

## Source Code Documentation

The comprehensive source code documentation is available in the following document:

[Code Documentation](https://docs.google.com/document/d/1example-link-to-your-code-doc/edit)

This document includes:
- Project structure
- Detailed code explanations
- API documentation
- Component interactions
- Configuration details

## Additional Resources

- [Figma Design](https://www.figma.com/file/QHpASp7wGRRcjh0oxCuspL/FullStack-Engineer-Internship-Assignment?type=design&node-id=0-1&mode=design&t=geu9rfpXEecN8eFZ-0) - Original design specifications
- [GitHub Repository](https://github.com/yourusername/pdf-qa-application) - Source code repository
- [API Documentation](https://work-1-mlwrmwhcbesatuqv.prod-runtime.all-hands.dev:12000/docs) - FastAPI auto-generated documentation

## Running the Application Locally

To run the application locally:

1. Clone the repository
2. Navigate to the project root directory
3. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ```
4. Run the application using the provided script:
   ```
   ./run.sh
   ```
5. Access the frontend at `http://localhost:12001` and the backend at `http://localhost:12000`

## Features Implemented

- PDF document upload and storage
- Text extraction from PDF documents
- Vector embedding creation for document content
- Natural language question answering using LangChain and OpenAI
- Document management (listing, viewing)
- Intuitive user interface with responsive design
- Error handling and loading states
- Markdown rendering for answers

## Technologies Used

### Backend
- FastAPI
- SQLAlchemy
- LangChain
- OpenAI
- FAISS
- PyMuPDF

### Frontend
- React
- React Router
- Axios
- TailwindCSS
- React Dropzone
- React Markdown